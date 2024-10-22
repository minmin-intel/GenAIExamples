from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import argparse
import pandas as pd
import os
import json
from agents.tools import get_tools
from agents.prompt import *

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--query_file", type=str, required=True)
    parser.add_argument("--kw_file", type=str)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--multiagent", action="store_true")
    parser.add_argument("--critic", action="store_true")
    parser.add_argument("--sql_agent", action="store_true")
    parser.add_argument("--sql_agent_fixer", action="store_true")
    parser.add_argument("--sql_agent_hint_fixer", action="store_true")
    parser.add_argument("--hier_sql_agent", action="store_true")
    parser.add_argument("--db_name", type=str, default="california_schools")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    return args


def get_trace(messages):
    trace = []
    for m in messages:
        if isinstance(m, AIMessage):
            try:
                tool_calls = m.tool_calls
                trace.append(m.content)
                trace.append(tool_calls)
            except:
                trace.append(m.content)
        if isinstance(m, ToolMessage):
            trace.append(m.content)
    return trace


def get_num_llm_calls(messages):
    count = 0
    for m in messages:
        if isinstance(m, AIMessage):
            count += 1
    return count

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
        n = get_num_llm_calls(s["messages"])
        return message.content, trace, n
    
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", None, None


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
    res, _, _ = run_agent(agent_executor, query, recursion_limit=15)
    return res


@tool
def query_database_with_sql_agent(query:str)->str:
    '''Use a SQL database agent to query the database. Query should be in natural language.'''
    print("@@@@@@ Running SQL agent to get the answer....")
    initial_state = sql_agent_fixer.prepare_initial_state(query)
    res, _, _ = run_agent(sql_agent_fixer_executor, initial_state, recursion_limit=16)
    return res


def save_json_lines(json_lines, args):
    outfile = "sql_agent_results.json"
    output = os.path.join(args.output, outfile)
    with open(output, "w") as f:
        for line in json_lines:
            f.write(str(line)+"\n")


if __name__ == "__main__":
    args = get_args()
    
    llm = ChatOpenAI(model=args.model, temperature=0)
    if args.multiagent:
        from agents.tools import search_web
        tools = [query_sql_database, search_web]
        system_message = SystemMessage(content=V4_SYSM)
    elif args.critic:
        tools = get_tools(args, llm)
        system_message = SystemMessage(content=V7_SYSM)
    elif args.sql_agent:
        from agents.tools import get_tools_sql_agent
        tools = get_tools_sql_agent(args)
    elif args.hier_sql_agent:
        from agents.tools import search_web
        from agents.sql_agent import SQLAgent, SQLAgentWithQueryFixer, SQLAgentWithHintAndQueryFixer
        from agents.tools import get_tools_sql_agent
        db_query_tool = get_tools_sql_agent(args)[0]
        global sql_agent_fixer
        global sql_agent_fixer_executor
        # sql_agent_fixer = SQLAgent(args, [db_query_tool])
        # sql_agent_fixer = SQLAgentWithQueryFixer(args, [db_query_tool])
        sql_agent_fixer = SQLAgentWithHintAndQueryFixer(args, [db_query_tool])
        sql_agent_fixer_executor = sql_agent_fixer.app
        tools = [query_database_with_sql_agent, search_web]
        system_message = SystemMessage(content=V10_SYSM)
    elif args.sql_agent_fixer or args.sql_agent_hint_fixer:
        # from agents.tools import search_web
        # from agents.sql_agent import SQLAgentWithHintAndQueryFixer
        from agents.tools import get_tools_sql_agent
        # db_query_tool = get_tools_sql_agent(args)[0]
        # tools = [query_database_with_sql_agent, search_web]
        # system_message = SystemMessage(content=V10_SYSM)
        # global sql_agent_fixer
        # global sql_agent_fixer_executor
        # sql_agent_fixer = SQLAgentWithQueryFixer(args, [db_query_tool])
        # sql_agent_fixer_executor = sql_agent_fixer.app
        # temp_tools = get_tools_sql_agent(args)
        # tools = [temp_tools[0]] # only use the db_query_tool
        tools = get_tools_sql_agent(args)
    else:
        tools = get_tools(args, llm)
        system_message = SystemMessage(content=V6_SYSM)

    print("Tools: ", tools)

    if args.critic:
        from agents.critic_agent import AgentWithCritic
        agent = AgentWithCritic(args, tools)
        agent_executor = agent.app
    elif args.sql_agent:
        from agents.sql_agent import SQLAgent
        agent = SQLAgent(args, tools)
        agent_executor = agent.app
    elif args.sql_agent_fixer:
        from agents.sql_agent import SQLAgentWithQueryFixer
        agent = SQLAgentWithQueryFixer(args, tools)
        agent_executor = agent.app
    elif args.sql_agent_hint_fixer:
        from agents.sql_agent import SQLAgentWithHintAndQueryFixer
        agent = SQLAgentWithHintAndQueryFixer(args, tools)
        agent_executor = agent.app
    else:
        print(f"Creating agent with tools {tools} and sysm {system_message}....")
        agent_executor = create_react_agent(llm, tools, state_modifier=system_message)

    df = pd.read_csv(args.query_file)
    
    # query= [
    #     # "What is the telephone number for the school with the lowest average score in reading in Southern California?",
    #     # "Please list the top three continuation schools with the lowest eligible free rates for students aged 5-17 and rank them based on the overall affordability of their respective cities.",
    #     # "Of the cities containing exclusively virtual schools which are the top 3 safest places to live?",
    #     # "How many test takers are there at the school/s in a county with population over 2 million?",
    #     # "What are the two most common first names among the female school administrators?",
    #     # "Among the cities with the top 10 lowest enrollment for students in grades 1 through 12, which are the top 2 most popular cities to visit?",
    #     # "Of the schools with the top 3 SAT excellence rate, which county of the schools has the strongest academic reputation?",
    #     # "How many schools have the difference in enrollements between K-12 and ages 5-17 as more than average high school class size?",
    #     "Summarize the qualities of the schools with an average score in Math under 600 in the SAT test and are exclusively virtual.",
    #     ]
    # df = pd.DataFrame({"Query": query, "Answer": ["no answer"]*len(query)})

    recursion_limit = 25
    results = []
    traces = []
    num_llm_calls = []
    json_lines = []
    for _, row in df.iterrows():
        query = row["Query"]
        ref_answer = row["Answer"]
        if args.critic or args.sql_agent or args.sql_agent_fixer or args.sql_agent_hint_fixer:
            input = agent.prepare_initial_state(query)
        else:
            input = {"messages": [HumanMessage(content=query)]}
        print("******Input:\n", input)
        res, trace, n = run_agent(agent_executor, input, recursion_limit=recursion_limit)
        print("******Answer:\n", res)
        results.append(res)
        traces.append(trace)
        num_llm_calls.append(n)
        # print("******Trace: ", trace)
        json_lines.append({"query": query,"answer":ref_answer, "agent_answer": res, "trace": trace, "num_llm_calls": n})
        save_json_lines(json_lines, args)
        print("-"*50)
    
    df["agent_answer"] = results
    df["trace"] = traces
    df["num_llm_calls"] = num_llm_calls

    # save the results
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    outfile = args.query_file.split("/")[-1].replace("query", "v13_result_{}".format(args.model))
    
    df.to_csv(os.path.join(args.output, outfile), index=False)

    print("Results saved to: ", os.path.join(args.output, outfile))