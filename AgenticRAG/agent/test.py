from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from tools.tools import get_all_available_tools
from tools.tools import search_knowledge_base, get_grammy_award_count_by_artist, get_artist_all_works
from model import setup_hf_tgi_client
import argparse
import json

RECURSION_LIMIT = 5

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


def init_agent(args, tools):
    if args.agent_type=="react":
        model = setup_hf_tgi_client(args)
        # model = ChatOpenAI(model="gpt-4o", temperature=0)
        graph = create_react_agent(model, tools = tools)
    elif args.agent_type=='doc_grader':
        from agent import RAGAgentwithLanggraph
        graph = RAGAgentwithLanggraph(args, tools).app
    else:
        pass
    return graph


def run_agent(query, query_time, graph):
    # graph.step_timeout = 1200
    prompt = "Query: {} \n Query Time: {}".format(query, query_time)
    print("Prompt:\n{}".format(prompt))
    inputs = {"messages": [("user", prompt)]}
    try:
        for s in graph.stream(inputs, {"recursion_limit": RECURSION_LIMIT}, stream_mode="values"):
            # message = s["messages"][-1]
            # if isinstance(message, tuple):
            #     print(message)
            # else:
            #     message.pretty_print()
            for k, v in s.items():
                print("{}: {}".format(k,v))

        # response = s["messages"][-1]
        response = s['output']
        print('***Final output:\n{}'.format(response))
    except Exception as e:
        print("***Error: {}".format(e))
        response = str(e)
    
    print('***Total # messages: ',len(s["messages"]))
    print('-'*50)
    return response, s["messages"]

def get_messages_content(messages):
    print('Get message content...')
    output = []
    for m in messages:
        print(m)
        output.append(m.content)
        print('-'*50)
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--llm_endpoint_url", type=str, default="localhost:8080")
    parser.add_argument("--agent_type", type=str, default="doc_grader")
    parser.add_argument("--model_id", type=str, default="meta-llama/Meta-Llama-3-8B-Instruct")
    parser.add_argument("--max_new_tokens", type=int, default=256)
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

    # tools = get_all_available_tools()
    # tools=[search_knowledge_base, get_grammy_award_count_by_artist, get_artist_all_works]
    tools = [search_knowledge_base]
    
    graph = init_agent(args, tools)

    output = []
    for q, t in zip(query_list, query_time):
        res, messages = run_agent(q, t, graph)
        output.append(
            {
                "query": q,
                "query_time": t,
                "response": res,
                # "messages": get_messages_content(messages)
            }
        )
    
    with open("/home/user/datasets/crag_results/agent_test_output.jsonl", "w") as f:
        for line in output:
            f.write(json.dumps(line) + "\n")
        


