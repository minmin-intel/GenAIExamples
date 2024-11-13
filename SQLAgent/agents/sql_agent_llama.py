from typing import Annotated, Sequence, TypedDict
import json
import os

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep
from langgraph.prebuilt import ToolNode
from langchain_community.utilities import SQLDatabase

from sentence_transformers import SentenceTransformer
try:
    from .prompt_llama import *
    from .hint import generate_column_descriptions, pick_hints
    from .utils import convert_json_to_tool_call, assemble_history_with_feedback, assemble_history, remove_repeated_tool_calls
    from .utils import LlamaOutputParser, LlamaOutputParserAndQueryFixer

except:
    from prompt_llama import *
    from hint import generate_column_descriptions, pick_hints
    from utils import convert_json_to_tool_call, assemble_history_with_feedback, assemble_history, remove_repeated_tool_calls
    from utils import LlamaOutputParser, LlamaOutputParserAndQueryFixer


def setup_tgi(args):
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

    generation_params = {
        "max_new_tokens": args.max_new_tokens,
        "top_k": args.top_k,
        "top_p": args.top_p,
        "temperature": args.temperature,
        "repetition_penalty": args.repetition_penalty,
        "return_full_text": False,
        "streaming": False,
    }

    print(generation_params)

    llm = HuggingFaceEndpoint(
        endpoint_url=args.llm_endpoint_url,
        task="text-generation",
        **generation_params,
    )
    return llm
    # chat_model = ChatHuggingFace(llm=llm, model_id=args.model)
    # return chat_model


def setup_chat_model(args):
    from langchain_openai import ChatOpenAI

    openai_endpoint = f"{args.llm_endpoint_url}/v1"
    params = {
        "temperature": args.temperature,
        "max_tokens": args.max_new_tokens,
        "streaming": False,
    }
    llm = ChatOpenAI(openai_api_key="EMPTY", openai_api_base=openai_endpoint, model_name=args.model, **params)
    return llm


def tool_renderer(tools):
    tool_strings = []
    for tool in tools:
        description = f"{tool.name} - {tool.description}"

        arg_schema = []
        for k, tool_dict in tool.args.items():
            k_type = tool_dict["type"] if "type" in tool_dict else ""
            k_desc = tool_dict["description"] if "description" in tool_dict else ""
            arg_schema.append(f"{k} ({k_type}): {k_desc}")

        tool_strings.append(f"{description}, args: {arg_schema}")
    return "\n".join(tool_strings)


def tool_renderer_exclude_sql_query(tools):
    tool_strings = []
    for tool in tools:
        if tool.name == "sql_db_query":
            pass
        else:
            description = f"{tool.name} - {tool.description}"

            arg_schema = []
            for k, tool_dict in tool.args.items():
                k_type = tool_dict["type"] if "type" in tool_dict else ""
                k_desc = tool_dict["description"] if "description" in tool_dict else ""
                arg_schema.append(f"{k} ({k_type}): {k_desc}")

            tool_strings.append(f"{description}, args: {arg_schema}")
    return "\n".join(tool_strings)


def get_table_schema(db_name):
    working_dir = os.getenv("WORKDIR")
    DBPATH=f"{working_dir}/TAG-Bench/dev_folder/dev_databases/{db_name}/{db_name}.sqlite"
    uri= "sqlite:///{path}".format(path=DBPATH)
    db = SQLDatabase.from_uri(uri)
    table_names = ", ".join(db.get_usable_table_names())
    num_tables = len(table_names.split(","))
    schema = db.get_table_info_no_throw([t.strip() for t in table_names.split(",")])
    return schema, num_tables


class AgentState(TypedDict):
    """The state of the agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    hint: str

    
class AgentNodeLlama:
    def __init__(self, args, tools):
        self.llm = setup_chat_model(args)
        self.args = args
        # self.tools = tool_renderer(tools)
        self.tools = tool_renderer_exclude_sql_query(tools)
        print("@@@@ Tools: ", self.tools)
        # output_parser=LlamaOutputParser()
        # self.chain= self.llm | output_parser
        self.chain = self.llm
        # self.output_parser = LlamaOutputParser(chat_model = self.llm)
        self.output_parser = LlamaOutputParserAndQueryFixer(chat_model = self.llm)

        # for generating hints
        self.cols_descriptions, self.values_descriptions = generate_column_descriptions(db_name=args.db_name)
        self.embed_model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        self.column_embeddings = self.embed_model.encode(self.values_descriptions)
        


    def __call__(self, state):
        print("----------Call Agent Node----------")
        question = state["messages"][0].content
        table_schema, num_tables = get_table_schema(self.args.db_name)
        if not state["hint"]:
            hints = pick_hints(question, self.embed_model,self.column_embeddings,self.cols_descriptions)
        else:
            hints = state["hint"]
        print("@@@ Hints: ", hints)
        if self.args.strategy == "sql_fixer_llama":
            history = assemble_history_with_feedback(state["messages"], self.llm)
        elif self.args.strategy == "sql_agent_llama":
            history = assemble_history(state["messages"])
        print("@@@ History: ", history)
        # feedback = state["feedback"]
        # print("@@@ Feedback: ", feedback)
        prompt = AGENT_NODE_TEMPLATE.format(
            domain=self.args.db_name,
            tools = self.tools,
            num_tables=num_tables,
            tables_schema=table_schema, 
            question=question, 
            hints=hints,
            history=history,
            # feedback=feedback
            )
        
        output = self.chain.invoke(prompt)
        output = self.output_parser.parse(output.content, history, table_schema, hints, question) #text: str, history: str, db_schema: str, hint: str
        print("@@@@@ Agent output:\n", output)

        # convert output to tool calls
        tool_calls = []
        for res in output:
            if "tool" in res:
                tool_call = convert_json_to_tool_call(res)
                tool_calls.append(tool_call)

        # check if same tool calls have been made before
        # if yes, then remove the repeated tool calls
        if tool_calls:
            new_tool_calls = remove_repeated_tool_calls(tool_calls, state["messages"])
            print("@@@@ New Tool Calls:\n", new_tool_calls)
        else:
            new_tool_calls = []

        if new_tool_calls:
            ai_message = AIMessage(content="", tool_calls=new_tool_calls)
        elif tool_calls:
            ai_message = AIMessage(content="Repeated previous steps.", tool_calls=tool_calls)
        elif "answer" in output[0]:
            ai_message = AIMessage(content=str(output[0]["answer"]))
        else:
            ai_message = AIMessage(content=str(output))
        
        return {"messages": [ai_message], "hint": hints}



class QueryFixerNode:
    def __init__(self, args):
        llm = setup_tgi(args)
        prompt = PromptTemplate(
            template=QUERYFIXER_PROMPT_v4,
            input_variables=["DATABASE_SCHEMA", "QUESTION", "HINT", "QUERY", "RESULT"],
        )
        self.chain = prompt | llm
        self.args = args
    
    def get_sql_query_and_result(self, state):
        messages = state["messages"]
        assert isinstance(messages[-1], ToolMessage), "The last message should be a tool message"
        result = messages[-1].content
        id = messages[-1].tool_call_id
        query = ""
        question = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                if msg.tool_calls[0]["id"] == id:
                    query = msg.tool_calls[0]["args"]["query"]
                    question = msg.content
                    break
        print("@@@@ Executed SQL Query: ", query)
        print("@@@@ Execution Result: ", result)
        return query, result, question

    def __call__(self, state):
        """
        **************************
        Table creation statements
        {DATABASE_SCHEMA}
        **************************
        Hint:
        {HINT}
        **************************
        The original question is:
        Question:
        {QUESTION}
        The SQL query executed was:
        {QUERY}
        The execution result:
        {RESULT}
        **************************
        """
        print("----------Call Query Fixer Node----------")
        table_schema, _ = get_table_schema(self.args.db_name)
        question = state["messages"][0].content
        hint = state["hint"]
        query, result, thought = self.get_sql_query_and_result(state)
        response = self.chain.invoke(
            {
                "DATABASE_SCHEMA": table_schema,
                "QUESTION": question,
                "HINT": hint,
                "QUERY": query,
                "RESULT": result,
            }
        )
        print("@@@@@ Query fixer output:\n", response)
        msg = HumanMessage(content=response)
        return {"messages":[msg],"feedback": response}

class SQLAgentWithQueryFixerLLAMA:
    """
    can only have one tool - sql_db_query tool
    """
    def __init__(self, args, tools):
        agent = AgentNodeLlama(args, tools)
        query_fixer = QueryFixerNode(args)
        tool_node = ToolNode(tools)

        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("agent", agent)
        workflow.add_node("query_fixer", query_fixer)
        workflow.add_node("tools", tool_node)

        workflow.set_entry_point("agent")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            self.should_continue,
            # Finally we pass in a mapping.
            # The keys are strings, and the values are other nodes.
            # END is a special node marking that the graph should finish.
            # What will happen is we will call `should_continue`, and then the output of that
            # will be matched against the keys in this mapping.
            # Based on which one it matches, that node will then be called.
            {
                # If `tools`, then we call the tool node.
                "continue": "tools",
                "end": END,
            },
        )

        # workflow.add_edge("tools", "query_fixer")
        workflow.add_conditional_edges(
            "tools",
            self.should_go_to_query_fixer,
            {
                "true": "query_fixer",
                "false": "agent"
            },
        )
        workflow.add_edge("query_fixer", "agent")

        self.app = workflow.compile()
        

    # Define the function that determines whether to continue or not
    def should_continue(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"
        

    def should_go_to_query_fixer(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        assert isinstance(last_message, ToolMessage), "The last message should be a tool message"
        print("@@@@ Called Tool: ", last_message.name)
        if last_message.name == "sql_db_query":
            print("@@@@ Going to Query Fixer")
            return "true"
        else:
            print("@@@@ Going back to Agent")
            return "false"
    
    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)], "is_last_step": IsLastStep(False), "hint": "", "feedback": ""}

class SQLAgentLLAMA:
    def __init__(self, args, tools):
        agent = AgentNodeLlama(args, tools)
        tool_node = ToolNode(tools)

        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("agent", agent)
        workflow.add_node("tools", tool_node)

        workflow.set_entry_point("agent")

        # We now add a conditional edge
        # workflow.add_conditional_edges(
        #     "agent",
        #     self.should_continue,
        #     {
        #         # If `tools`, then we call the tool node.
        #         "continue": "tools",
        #         "end": END,
        #     },
        # )

        workflow.add_conditional_edges(
            "agent",
            self.decide_next_step,
            {
                # If `tools`, then we call the tool node.
                "tools": "tools",
                "agent": "agent",
                "end": END,
            },
        )

        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge("tools", "agent")

        self.app = workflow.compile()
        

    # Define the function that determines whether to continue or not
    def should_continue(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"
        
    def decide_next_step(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls and last_message.content == "Repeated previous steps.":
            print("@@@@ Repeated tool calls from previous steps, go back to agent")
            return "agent"
        elif last_message.tool_calls and last_message.content != "Repeated previous steps.":
            print("@@@@ New Tool calls, go to tools")
            return "tools"
        else:
            return "end"
    
    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)], "is_last_step": IsLastStep(False), "hint": ""}




if __name__ == "__main__":
    import argparse
    import pandas as pd
    from tools import get_tools_sql_agent

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="meta-llama/Llama-3.1-70B-Instruct")
    parser.add_argument("--db_name", type=str, default="california_schools")
    parser.add_argument("--llm_endpoint_url", type=str, default="http://localhost:8085")
    parser.add_argument("--max_new_tokens", type=int, default=8192)
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--temperature", type=float, default=0.01)
    parser.add_argument("--repetition_penalty", type=float, default=1.03)
    parser.add_argument("--tgi_llama", action="store_true")
    parser.add_argument("--vllm", action="store_true")

    args = parser.parse_args()


    tools = get_tools_sql_agent(args)
    agent_node = AgentNodeLlama(args, tools)

    query="What is the telephone number for the school with the lowest average score in reading in Southern California?"
    state = {
            "messages": [HumanMessage(content=query)],
            "is_last_step": IsLastStep(False),
            "hint": "",
            "feedback": ""
        }
    
    print(agent_node(state))


    # df = pd.read_csv(f"{os.getenv('WORKDIR')}/TAG-Bench/query_by_db/query_california_schools.csv")
    
    # for _, row in df.iterrows():
    #     query = row["Query"]
    #     print("Query: ", query)
    #     state = {
    #         "messages": [HumanMessage(content=query)],
    #         "is_last_step": IsLastStep(False),
    #         "hint": ""
    #     }
        
    #     print("=="*20)
    
    # df.to_csv(f"{os.getenv('WORKDIR')}/sql_agent_output/test_results.csv", index=False)
    