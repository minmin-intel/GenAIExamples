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
from prompt import V7_SYSM
import json

class AgentState(TypedDict):
    """The state of the agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    critic_decision: str
    num_critic: int
    is_last_step: IsLastStep


class AgentNode:
    """Do planning and reasoning and generate tool calls.

    A workaround for open-source llm served by TGI-gaudi.
    """

    def __init__(self, args, tools):
        
        self.llm = ChatOpenAI(model=args.model,temperature=0).bind_tools(tools)
        

    def __call__(self, state):
        _system_message = SystemMessage(content=V7_SYSM)
        state_modifier_runnable = RunnableLambda(
            lambda state: [_system_message] + state["messages"],
            name="StateModifier",
        )

        chain = state_modifier_runnable | self.llm
        response = chain.invoke(state)
        return {"messages": [response]}


def assemble_history(messages):
    """
    messages: AI, TOOL, AI, TOOL, etc.
    """
    query_history = ""
    n = 1
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    query_history += f"Tool Call: {tool} - {tc_args}\n"
            else:
                # did not make tool calls
                query_history += f"Agent Output: {m.content}\n"
        # elif isinstance(m, ToolMessage):
        #     query_history += f"Tool Output: {m.content}\n\n"
        elif isinstance(m, HumanMessage):
            query_history += f"Critic feedback: {m.content}\n"
    return query_history


class CriticNode:
    def __init__(self, args):
        from prompt import CRITIC_PROMPT
        llm = ChatOpenAI(model=args.model,temperature=0)
        prompt = PromptTemplate(
            template=CRITIC_PROMPT,
            input_variables=["input", "history"],
        )
        self.chain = prompt | llm
        

    def __call__(self, state):
        messages = state["messages"]
        query = messages[0].content
        print("@@@@@ User Query:\n", query)
        agent_answer = messages[-1].content
        print("@@@@@ Agent Answer:\n", agent_answer)
        history = assemble_history(messages)
        print("@@@@@ History:\n", history)
        response = self.chain.invoke({"input": query, "history": history}).content
        print("@@@@@ Critic Response:\n", response)
        try:
            response = json.loads(response)
            if "suggestions" in response:
                return {"messages": [response["suggestions"]], "critic_decision": "continue", "num_critic": state["num_critic"] + 1}
            else:
                return {"messages": [response["answer"]], "critic_decision": "end", "num_critic": state["num_critic"] + 1}
        except Exception as e:
            print(f"Exception occurred in Critic node: {e}")
            return {"messages": [agent_answer], "critic_decision": "end","num_critic": state["num_critic"] + 1}


class GeneratorNode:
    def __init__(self, args):
        from prompt import GENERATOR_PROMPT
        llm = ChatOpenAI(model=args.model,temperature=0)
        prompt = PromptTemplate(
            template=GENERATOR_PROMPT,
            input_variables=["input", "agent_answer"],
        )
        self.chain = prompt | llm
        

    def __call__(self, state):
        messages = state["messages"]
        query = messages[0].content
        print("@@@@@ User Query:\n", query)
        agent_answer = messages[-1].content
        print("@@@@@ Agent Answer:\n", agent_answer)

        response = self.chain.invoke({"input": query, "agent_answer": agent_answer})
        print("@@@@@ Generator:\n", response)
        
        return {"messages": [response]}




class AgentWithCritic:
    def __init__(self, args, tools):
        agent = AgentNode(args, tools)
        tool_node = ToolNode(tools)
        critic = CriticNode(args)
        generator = GeneratorNode(args)

        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("agent", agent)
        workflow.add_node("tools", tool_node)
        workflow.add_node("critic", critic)
        workflow.add_node("generator", generator)

        workflow.set_entry_point("agent")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            self.decide_next_step,
            # Finally we pass in a mapping.
            # The keys are strings, and the values are other nodes.
            # END is a special node marking that the graph should finish.
            # What will happen is we will call `should_continue`, and then the output of that
            # will be matched against the keys in this mapping.
            # Based on which one it matches, that node will then be called.
            {
                # If `tools`, then we call the tool node.
                "continue": "tools",
                # Otherwise we go to critic.
                "should_critic": "critic",
                "end": "generator",
            },
        )

        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge("tools", "agent")

        workflow.add_edge("generator", END)

        workflow.add_conditional_edges(
            "critic",
            self.should_end,
            {
                "should_end": END,
                "should_continue": "agent",
            }
    
        )

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
    
    def should_end(self, state: AgentState):
        if state["critic_decision"] == "end":
            return "should_end"
        else:
            return "should_continue"
        
    def decide_next_step(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "continue"
        else:
            if state["num_critic"] >= 2 or state["critic_decision"] == "end":
                return "end"
            else:
                return "should_critic"

    def prepare_initial_state(self, query):
        return {"messages": [HumanMessage(content=query)], "critic_decision": "continue", "num_critic": 0}
