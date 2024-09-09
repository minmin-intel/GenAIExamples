from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import argparse
import pandas as pd
import os
from tools import get_tools
from prompt import SQL_PREFIX, V2_SYSM

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--query_file", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
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


def run_agent(agent_executor, query):
    try:
        for s in agent_executor.stream(
            {"messages": [HumanMessage(content=query)]},
            stream_mode="values",
            config={"recursion_limit": 20},
        ):
            message = s["messages"][-1]
            message.pretty_print()

        trace = get_trace(s["messages"])
        return message.content, trace
    
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", None


if __name__ == "__main__":
    args = get_args()
    
    llm = ChatOpenAI(model=args.model, temperature=0)
    tools = get_tools(args, llm)
    print("Tools: ", tools)
    system_message = SystemMessage(content=V2_SYSM)
    agent_executor = create_react_agent(llm, tools, state_modifier=system_message)

    df = pd.read_csv(args.query_file)
    # df = df.head(1)
    
    # query= [
    #     # "What is the telephone number for the school with the lowest average score in reading in Southern California?",
    #     "Of the cities containing exclusively virtual schools which are the top 3 safest places to live?",
    # ]
    # df = pd.DataFrame({"Query": query})

    results = []
    traces = []
    for _, row in df.iterrows():
        query = row["Query"]
        print("******Query: ", query)
        res, trace = run_agent(agent_executor, query)
        print("******Answer: ", res)
        results.append(res)
        traces.append(trace)
        # print("******Trace: ", trace)
        print("-"*50)
    
    df["agent_answer"] = results
    df["trace"] = traces

    # save the results
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    outfile = args.query_file.split("/")[-1].replace("query", "v3_result_{}".format(args.model))
    
    df.to_csv(os.path.join(args.output, outfile), index=False)

    print("Results saved to: ", os.path.join(args.output, outfile))