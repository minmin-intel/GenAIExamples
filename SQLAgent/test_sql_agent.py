from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import argparse
import pandas as pd
import os
from tools import get_tools
from prompt import *

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--query_file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--multiagent", action="store_true")
    parser.add_argument("--critic", action="store_true")
    args = parser.parse_args()
    return args


def get_trace(messages):
    trace = []
    for m in messages:
        if isinstance(m, AIMessage):
            try:
                tool_calls = m.additional_kwargs["tool_calls"]
                trace.append(tool_calls)
            except:
                trace.append(m.content)
        if isinstance(m, ToolMessage):
            trace.append(m.content)
    return trace


def run_agent(agent_executor, input, recursion_limit=10):
    try:

        for s in agent_executor.stream(
            input,
            stream_mode="values",
            config={"recursion_limit": recursion_limit},
        ):
            message = s["messages"][-1]
            message.pretty_print()

        trace = get_trace(s["messages"])
        return message.content, trace
    
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", None


from langchain_core.tools import tool
@tool
def query_sql_database(query:str)->str:
    '''Query the SQL database with natural language and get answer in natural language.\
    The database has data of California schools, SAT scores and Free and Reduced Price Meals (FRPM) data.\
    The database does NOT have geographical, census or gender data.\
    More likely to get answer with simple queries.'''
    print("@@@@@@ Running SQL agent to get the answer....")
    llm = ChatOpenAI(model=args.model, temperature=0)
    tools = get_tools(args, llm)
    print("Tools: ", tools)
    system_message = SystemMessage(content=V2_SYSM)
    agent_executor = create_react_agent(llm, tools, state_modifier=system_message)
    res, _ = run_agent(agent_executor, query, recursion_limit=15)
    return res



if __name__ == "__main__":
    args = get_args()
    
    llm = ChatOpenAI(model=args.model, temperature=0)
    if args.multiagent:
        from tools import search_web
        tools = [query_sql_database, search_web]
        system_message = SystemMessage(content=V4_SYSM)
    elif args.critic:
        tools = get_tools(args, llm)
        system_message = SystemMessage(content=V7_SYSM)

    else:
        tools = get_tools(args, llm)
        system_message = SystemMessage(content=V6_SYSM)

    print("Tools: ", tools)

    if args.critic:
        from agent import AgentWithCritic
        agent = AgentWithCritic(args, tools)
        agent_executor = agent.app
    else:
        agent_executor = create_react_agent(llm, tools, state_modifier=system_message)

    df = pd.read_csv(args.query_file)
    
    # query= [
    #     # "What is the telephone number for the school with the lowest average score in reading in Southern California?",
    #     # "Of the cities containing exclusively virtual schools which are the top 3 safest places to live?",
    #     # "How many test takers are there at the school/s in a county with population over 2 million?",
    #     # "What are the two most common first names among the female school administrators?",
    #     "Among the cities with the top 10 lowest enrollment for students in grades 1 through 12, which are the top 2 most popular cities to visit?",
    # ]
    # df = pd.DataFrame({"Query": query})

    recursion_limit = 30
    results = []
    traces = []
    for _, row in df.iterrows():
        query = row["Query"]
        if args.critic:
            input = agent.prepare_initial_state(query)
        else:
            input = {"messages": [HumanMessage(content=query)]}
        print("******Input:\n", input)
        res, trace = run_agent(agent_executor, input, recursion_limit=recursion_limit)
        print("******Answer:\n", res)
        results.append(res)
        traces.append(trace)
        # print("******Trace: ", trace)
        print("-"*50)
    
    df["agent_answer"] = results
    df["trace"] = traces

    # save the results
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    outfile = args.query_file.split("/")[-1].replace("query", "v7_result_{}".format(args.model))
    
    df.to_csv(os.path.join(args.output, outfile), index=False)

    print("Results saved to: ", os.path.join(args.output, outfile))