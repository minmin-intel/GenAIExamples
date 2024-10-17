from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
# from langgraph.checkpoint.memory import MemorySaver
from .prompt import *
import json
import os
from .hint import generate_hints, generate_column_descriptions
from sentence_transformers import SentenceTransformer
from langchain_community.utilities import SQLDatabase

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
    

class AgentNode:
    def __init__(self, args, tools):
        self.llm = ChatOpenAI(model=args.model,temperature=0).bind_tools(tools)
        self.cols_descriptions, self.values_descriptions = generate_column_descriptions(db_name=args.db_name)
        self.embed_model = SentenceTransformer('BAAI/bge-base-en-v1.5')
        self.column_embeddings = self.embed_model.encode(self.values_descriptions)
        self.args = args


    def __call__(self, state):
        print("----------Call Agent Node----------")
        question = state["messages"][0].content
        table_schema, num_tables = get_table_schema(self.args.db_name)
        hints = generate_hints(question, self.column_embeddings,self.cols_descriptions)
        sysm = V12_SYSM.format(num_tables=num_tables,tables_schema=table_schema, question=question, hints=hints)
        _system_message = SystemMessage(content=sysm)
        state_modifier_runnable = RunnableLambda(
            lambda state: [_system_message] + state["messages"],
            name="StateModifier",
        )
        # print(state_modifier_runnable.invoke(state))
        chain = state_modifier_runnable | self.llm
        response = chain.invoke(state)
        # print("===========")
        # print(response)
        return {"messages": [response], "hint": hints}


class QueryFixerNode:
    def __init__(self, args):
        from .prompt import QUERYFIXER_PROMPT
        llm = ChatOpenAI(model=args.model,temperature=0)
        prompt = PromptTemplate(
            template=QUERYFIXER_PROMPT_v2,
            input_variables=["DATABASE_SCHEMA", "QUESTION", "HINT", "QUERY", "RESULT"],
        )
        self.chain = prompt | llm
        self.args = args
    
    def get_sql_query_and_result(self, state):
        messages = state["messages"]
        assert isinstance(messages[-1], ToolMessage), "The last message should be a tool message"
        result = messages[-1].content
        assert isinstance(messages[-2], AIMessage), "The second last message should be AI message with tool call"
        query = messages[-2].tool_calls[0]["args"]["query"]
        print("@@@@ Executed SQL Query: ", query)
        print("@@@@ Execution Result: ", result)
        return query, result
    


    def __call__(self, state):
        """
        Table creation statements
        {DATABASE_SCHEMA}
        **************************
        The original question is:
        Question:
        {QUESTION}
        Evidence:
        {HINT}
        The SQL query executed was:
        {QUERY}
        The execution result:
        {RESULT}
        """
        print("----------Call Query Fixer Node----------")
        table_schema, _ = get_table_schema(self.args.db_name)
        question = state["messages"][0].content
        hint = state["hint"]
        query, result = self.get_sql_query_and_result(state)
        response = self.chain.invoke(
            {
                "DATABASE_SCHEMA": table_schema,
                "QUESTION": question,
                "HINT": hint,
                "QUERY": query,
                "RESULT": result,
            }
        )
        print("@@@@@ Query fixer output:\n", response.content)
        return {"messages": [response]}


    
class SQLAgent:
    def __init__(self, args, tools):
        agent = AgentNode(args, tools)
        tool_node = ToolNode(tools)

        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("agent", agent)
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
    
    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)], "is_last_step": IsLastStep(False), "hint": ""}


class SQLAgentWithQueryFixer:
    """
    can only have one tool - sql_db_query tool
    """
    def __init__(self, args, tools):
        agent = AgentNode(args, tools)
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

        workflow.add_edge("tools", "query_fixer")
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
        if last_message.tool_calls:
            return "true"
        else:
            return "false"
    
    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)], "is_last_step": IsLastStep(False), "hint": ""}






if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4o-mini-2024-07-18")
    parser.add_argument("--db_name", type=str, default="california_schools")

    args = parser.parse_args()
    from tools import get_tools_sql_agent

    # agent = AgentNode(args=args, tools=get_tools_sql_agent(args))
    agent = SQLAgent(args=args, tools=get_tools_sql_agent(args))

    query = "Of the schools with the top 3 SAT excellence rate, which county of the schools has the strongest academic reputation?"
    state = {
        "messages": [HumanMessage(content=query)],
        "is_last_step": IsLastStep(False),
    }

    initial_state = agent.prepare_initial_state(query)
