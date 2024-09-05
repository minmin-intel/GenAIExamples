from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import argparse
import pandas as pd
import os

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--query_file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    args = parser.parse_args()
    return args

def get_database(path):
    uri= "sqlite:///{path}".format(path=path)
    db = SQLDatabase.from_uri(uri)
    print(db.dialect)
    print(db.get_usable_table_names())
    return db


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


def run_agent(agent_executor, query):
    try:
        for s in agent_executor.stream(
            {"messages": [HumanMessage(content=query)]},
            stream_mode="values",
            config={"recursion_limit": 10},
        ):
            message = s["messages"][-1]
            message.pretty_print()

        trace = get_trace(s["messages"])
        return message.content, trace
    
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", None

SQL_PREFIX = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct SQLite query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

To start you should ALWAYS look at the tables in the database to see what you can query.
Do NOT skip this step.
Then you should query the schema of the most relevant tables."""


if __name__ == "__main__":
    args = get_args()
    db = get_database(args.path)
    system_message = SystemMessage(content=SQL_PREFIX)
    llm = ChatOpenAI(model=args.model, temperature=0)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    agent_executor = create_react_agent(llm, tools, state_modifier=system_message)

    df = pd.read_csv(args.query_file)
    # df = df.head(1)

    # query = "Among the schools with the average score in Math over 560 in the SAT test, how many schools are in the bay area?"
    
    results = []
    traces = []
    for _, row in df.iterrows():
        query = row["Query"]
        print("******Query: ", query)
        res, trace = run_agent(agent_executor, query)
        print("******Answer: ", res)
        results.append(res)
        traces.append(trace)
        print("******Trace: ", trace)
        print("-"*50)
    
    df["agent_answer"] = results
    df["trace"] = traces

    # save the results
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    outfile = args.query_file.split("/")[-1].replace("query", "result_{}".format(args.model))
    
    df.to_csv(os.path.join(args.output, outfile), index=False)

    print("Results saved to: ", os.path.join(args.output, outfile))