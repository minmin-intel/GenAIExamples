from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from tools.tools import get_all_available_tools
from tools.tools import search_knowledge_base, get_grammy_award_count_by_artist, get_artist_all_works
from model import setup_hf_tgi_client
import argparse
import json
import pandas as pd

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

def get_test_dataset(args):
    if args.query_file.endswith('.jsonl'):
        df = pd.read_json(args.query_file, lines=True, convert_dates=False)
    elif args.query_file.endswith('.csv'):
        df = pd.read_csv(args.query_file)
    else:
        raise ValueError("Invalid file format")
    return df

def init_agent(args, tools):
    if args.agent_type=="react":
        from prompt import REACT_SYS_MESSAGE
        if args.use_hf_tgi:
            model = setup_hf_tgi_client(args)
        else:
            model = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0)
        graph = create_react_agent(model, tools = tools, state_modifier=REACT_SYS_MESSAGE)
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

def get_total_tokens(messages):
    total_tokens = 0
    for m in messages:
        if isinstance(m, AIMessage):
            # total_tokens += m.response_metadata['token_usage']['total_tokens']
            total_tokens += m.usage_metadata["total_tokens"]
    return total_tokens
        

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

def run_agent(inputs, config, graph):
    # graph.step_timeout = 1200
    try:
        for s in graph.stream(inputs, config, stream_mode="values"):
            # message = s["messages"][-1]
            # if isinstance(message, tuple):
            #     print(message)
            # else:
            #     message.pretty_print()
            for k, v in s.items():
                print("*{}:\n{}".format(k,v))

        if "output" in s: # DocGrader
            # print('output key in state')
            context = get_last_tool_message(s["messages"])
            response = s['output']
        else:
            # print('output key not in state')
            response = s["messages"][-1].content
            context = get_trace(s["messages"])
        print('***Final output:\n{} \n****End of output****'.format(response))
        print('***Context:\n{} \n****End of context****'.format(context))
    except Exception as e:
        print("***Error: {}".format(e))
        response = str(e)
        context = None
    
    # count num of LLM calls
    # trace = get_trace(s["messages"])
    num_llm_calls = get_num_llm_calls(s["messages"])
    total_tokens = get_total_tokens(s["messages"])
    
    print('***Total # messages: ',len(s["messages"]))
    print('***Total # LLM calls: ', num_llm_calls)
    print('***Total # tokens: ', total_tokens)
    print('='*50)
    return response, context, num_llm_calls, total_tokens

def get_messages_content(messages):
    print('Get message content...')
    output = []
    for m in messages:
        print(m)
        output.append(m.content)
        print('-'*50)
    return output

def save_as_csv(output):
    df = pd.read_json(output, lines=True, convert_dates=False)
    df.to_csv(output.replace(".jsonl", ".csv"), index=False)

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
    parser.add_argument("--query_file", type=str, default="/home/user/datasets/crag_qas/crag_music_49queries_meta.csv", help="query file")
    args = parser.parse_args()
    print(args)

    RECURSION_LIMIT = 10

    # query_list, query_time = get_query(args)
    # query_list=["how many songs have been released by barbra streisand since winning he/she won their first grammy?"]
    # query_time=["03/21/2024, 23:37:29 PT"]
    # query_list = ["how many grammys has beyonc\u00e9 been nominated for?"]
    # query_time=["03/21/2024, 23:37:29 PT"]
    df = get_test_dataset(args)

    if args.agent_type=="react":
        tools = get_all_available_tools()
    elif args.agent_type=="doc_grader":
        tools = [search_knowledge_base]
    
    graph = init_agent(args, tools)
    config = {"recurison_limit": RECURSION_LIMIT}

    output = []
    
    n = 0
    for _, row in df.iterrows():
        q = row["query"]
        t = row["query_time"]
        prompt = "Question: {} \nThe question was asked at: {}".format(q, t)
        if args.agent_type=="react":   
            inputs = {
                "messages": [("user", prompt)],
            }
        elif args.agent_type=="doc_grader":
            inputs = {
                "messages": [("user", prompt)],
                "query_time": t
            }

        res, context, n, ntok = run_agent(inputs, config, graph)
        output.append(
            {
                "query": q,
                "query_time": t,
                "answer": res,
                "context": context,
                "num_llm_calls": n,
                "total_tokens": ntok,
                "ref_answer": row["answer"],
                "question_type": row["question_type"],
                "static_or_dynamic": row["static_or_dynamic"],
            }
        )
        # n+=1
        # if n>=2:
        #     break
    
    output_file = "/home/user/datasets/crag_results/crag_music_49queries_reactv0_gpt4omini_sysm_trace.jsonl"
    with open(output_file, "w") as f:
        for line in output:
            f.write(json.dumps(line) + "\n")
    
    save_as_csv(output_file)
