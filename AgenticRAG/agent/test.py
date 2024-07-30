from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from tools.tools import get_all_available_tools
from tools.tools import search_knowledge_base, get_grammy_award_count_by_artist, get_artist_all_works
from model import setup_hf_tgi_client
import argparse
import json

RECURSION_LIMIT = 10

def get_query(args):
    query = []
    query_time = []
    n = 0
    with open(args.query_file, "r") as f:
        for line in f:
            data = json.loads(line)
            query.append(data["query"])
            query_time.append(data["query_time"])
            # n += 1
            # if n >= 2:
            #     break
    return query, query_time


def init_agent(args, tools):
    if args.agent_type=="react":
        if args.use_hf_tgi:
            model = setup_hf_tgi_client(args)
        else:
            model = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0)
        graph = create_react_agent(model, tools = tools)
    elif args.agent_type=='doc_grader':
        # v0 
        # from agent import RAGAgentwithLanggraph
        # graph = RAGAgentwithLanggraph(args, tools).app

        # v1
        from agent import RAGAgentDocGraderV1
        graph = RAGAgentDocGraderV1(args, tools).app

    else:
        pass
    return graph


def get_last_tool_message(messages):
    for m in messages[::-1]:
        if isinstance(m, ToolMessage):
            return m.content
    return None

def get_num_llm_calls(messages):
    n_tool = 0
    for m in messages: # ToolMessage is not LLM call
        if isinstance(m, ToolMessage):
            n_tool += 1
    return len(messages) - n_tool - 1 # the first message is query, so subtract 1
            

def run_agent(query, query_time, graph):
    # graph.step_timeout = 1200
    prompt = "Question: {} \nThe question was asked at: {}".format(query, query_time)
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
                print("*{}:\n{}".format(k,v))

        # response = s["messages"][-1]
        if "output" in s:
            print('output key in state')
            response = s['output']
        else:
            print('output key not in state')
            response = s["messages"][-1].content
        context = get_last_tool_message(s["messages"])
        print('***Final output:\n{} \n****End of output****'.format(response))
        print('***Context:\n{} \n****End of context****'.format(context))
    except Exception as e:
        print("***Error: {}".format(e))
        response = str(e)
        context = None
    
    # count num of LLM calls
    num_llm_calls = get_num_llm_calls(s["messages"])
    
    print('***Total # messages: ',len(s["messages"]))
    print('='*50)
    return response, context, num_llm_calls

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
    parser.add_argument("--agent_type", type=str, default="react")
    parser.add_argument("--model_id", type=str, default="meta-llama/Meta-Llama-3.1-8B-Instruct")
    parser.add_argument("--max_new_tokens", type=int, default=256)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--repetition_penalty", type=float, default=1.2)
    parser.add_argument("--return_full_text", type=bool, default=False)
    parser.add_argument("--streaming", type=bool, default=False)
    parser.add_argument("--use_openai", type=bool, default=True)
    parser.add_argument("--use_hf_tgi", type=bool, default=False)
    parser.add_argument("--query_file", type=str, default="/home/user/datasets/crag_qas/crag_qa_music_sampled_low_relevance_score_with_query_time.jsonl", help="query jsonl file")
    args = parser.parse_args()

    print(args)

    query_list, query_time = get_query(args)
    # print(query_list)

    # query_list=["how many songs have been released by barbra streisand since winning he/she won their first grammy?"]
    # query_time=["03/21/2024, 23:37:29 PT"]

    # query_list = ["how many grammys has beyonc\u00e9 been nominated for?"]
    # query_time=["03/21/2024, 23:37:29 PT"]

    tools = get_all_available_tools()
    # tools=[search_knowledge_base, get_grammy_award_count_by_artist, get_artist_all_works]
    # tools = [search_knowledge_base]
    
    graph = init_agent(args, tools)

    output = []
    for q, t in zip(query_list, query_time):
        res, context, n = run_agent(q, t, graph)
        output.append(
            {
                "query": q,
                "query_time": t,
                "answer": res,
                "context": context,
                "num_llm_calls": n
            }
        )
    
    with open("/home/user/datasets/crag_results/crag_music_49queries_reactv0_gpt4omini.jsonl", "w") as f:
        for line in output:
            f.write(json.dumps(line) + "\n")
        


