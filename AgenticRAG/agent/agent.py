from langgraph.prebuilt import create_react_agent
from tools.tools import get_all_available_tools
from model import setup_hf_tgi_client
import argparse
import json


def get_query(args):
    query = []
    query_time = []
    n = 0
    with open(args.query_file, "r") as f:
        for line in f:
            data = json.loads(line)
            query.append(data["query"])
            query_time.append(data["query_time"])
            n += 1
            if n >= 2:
                break
    return query, query_time


def run_agent(query, query_time, graph):
    prompt = "Query: {} \n Query Time: {}".format(query, query_time)
    print("Prompt:\n{}".format(prompt))
    inputs = {"messages": [("user", prompt)]}
    for s in graph.stream(inputs, stream_mode="values"):
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
    response = s["messages"][-1]
    print('Response:\n{}'.format(response))
    print('-'*50)
    return response



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--llm_endpoint_url", type=str, default="localhost:8080")
    parser.add_argument("--model_id", type=str, default="Intel/neural-chat-7b-v3-3")
    parser.add_argument("--max_new_tokens", type=int, default=100)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--repetition_penalty", type=float, default=1.2)
    parser.add_argument("--return_full_text", type=bool, default=False)
    parser.add_argument("--streaming", type=bool, default=False)
    parser.add_argument("--query_file", type=str, default="/home/user/datasets/crag_qas/crag_qa_music_sampled_with_query_time.jsonl", help="query jsonl file")
    args = parser.parse_args()
    print(args)

    query_list, query_time = get_query(args)
    print(query_list)

    tools = get_all_available_tools()
    model = setup_hf_tgi_client(args)
    graph = create_react_agent(model, tools=tools)

    for q, t in zip(query_list, query_time):
        res = run_agent(q, t, graph)
        

