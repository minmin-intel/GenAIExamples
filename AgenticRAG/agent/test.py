from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from tools.tools import get_all_available_tools
from model import setup_hf_tgi_client
import argparse
import json
import pandas as pd
from utils import get_test_dataset, save_as_csv, save_results

NUM_LLM_CALLS_BY_RETRIEVAL_TOOL = 0

def init_agent(args, tools):
    if "react" in args.agent_type:
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
            try:
                if m.usage_metadata["total_tokens"]:
                    total_tokens += m.usage_metadata["total_tokens"]
                else:
                    total_tokens += m.response_metadata['token_usage']['total_tokens']
            except:
                total_tokens = 0
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
        for s in graph.stream(inputs, config=config, stream_mode="values"):
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
    
    # get statistics
    try:
        num_llm_calls = get_num_llm_calls(s["messages"])
        total_tokens = get_total_tokens(s["messages"])
        print('***Total # messages: ',len(s["messages"]))
        print('***Total # LLM calls: ', num_llm_calls)
        print('***Total # tokens: ', total_tokens)
    except:
        num_llm_calls = None
        total_tokens = None
    print('='*50)
    return response, context, num_llm_calls, total_tokens

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--llm_endpoint_url", type=str, default="localhost:8080")
    parser.add_argument("--agent_type", type=str, default="react")
    parser.add_argument("--use_all_tools", type=bool, default=False)
    parser.add_argument("--use_advanced_retrieval", type=bool, default=True)
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
    parser.add_argument("--embed_model", type=str, default="BAAI/bge-base-en-v1.5", help="embedding model for tools selection")
    parser.add_argument("--k", type=int, default=5, help="num of tools to be selected")
    parser.add_argument("--query_file", type=str, default="/home/user/datasets/crag_qas/crag_music_49queries_meta.csv", help="query file")
    parser.add_argument("--quick_test", type=bool, default=True)
    args = parser.parse_args()
    print(args)

    RECURSION_LIMIT = 3
    config = {"recursion_limit": RECURSION_LIMIT}

    if args.quick_test:
        # query=["how many songs have been released by barbra streisand since winning he/she won their first grammy?"]
        # query_time=["03/21/2024, 23:37:29 PT"]
        # query = "who has had more number one hits on the us billboard r&b/hip-hop songs chart, janet jackson or aretha franklin?"
        query_time = "03/13/2024, 09:42:59 PT"
        # query = "what is the most popular song on billboard in 2024-02-28?"
        query = "who has had more number one hits on the us billboard hot 100 chart, michael jackson or elvis presley?"
        # query = "when did dolly parton's song, blown away, come out?"
        # query = "who has played drums for the red hot chili peppers?"
        df = pd.DataFrame({"query": [query], "query_time": [query_time]})
    else:
        df = get_test_dataset(args)

    output = []
    output_dir = "/home/user/datasets/crag_results/"
    filename = "crag_music_49queries_react_selecttool_gpt4omini.jsonl"
    output_file = output_dir + filename


    if args.use_advanced_retrieval:
        from agent import RetrievalDocGrader
        from langchain_core.tools import tool

        retrieval_agent = RetrievalDocGrader(args).app
        @tool
        def search_knowledge_base(query:str)->str:
            '''Search knowledge base for a given query. Returns text related to the query.'''

            inputs = {
                "messages": [("user", query)],
                "relevant":"",
                "not_relevant":"",
                "num_retrieve":0,
                "num_rewrites":0,
                "num_grade":0
            }
            
            for s in retrieval_agent.stream(inputs, config={"recursion_limit": 10}, stream_mode="values"):
                for k, v in s.items():
                    print("**RETRIEVAL TOOL** {}:\n{}".format(k,v))

            context = s["relevant"]
            print('**Retrieval Tool output: ', context)
            global NUM_LLM_CALLS_BY_RETRIEVAL_TOOL
            NUM_LLM_CALLS_BY_RETRIEVAL_TOOL += (s["num_rewrites"]+s['num_grade'])
            if context:    
                return context
            else:
                ret = "No relevant information found in the knowledge base."
                print("****"+ret)
                return ret
            

    else:
        from tools.tools import search_knowledge_base

        
    if args.agent_type=="react_tool_selection":
        from sentence_transformers import SentenceTransformer
        from tool_selection import get_tools_descriptions,select_tools_for_query, get_selected_tools
        tools_descriptions = get_tools_descriptions()
        model = SentenceTransformer(args.embed_model)
        tools_embeddings = model.encode(tools_descriptions)
        output = []
        for _, row in df.iterrows():
            query = row["query"]
            # select tools based on query
            top_k_tools = select_tools_for_query(query, tools_embeddings, model, args.k, tools_descriptions)
            print('****Selected tools: ', top_k_tools)
            selected_tools = get_selected_tools(top_k_tools) # top k APIs
            selected_tools.append(search_knowledge_base) # always include retrieval tool
            # create react agent with selected tools
            graph = init_agent(args, selected_tools)
            # run agent
            q = row["query"]
            t = row["query_time"]
            prompt = "Question: {} \nThe question was asked at: {}".format(q, t)
            inputs = {
                "messages": [("user", prompt)],
            }
            res, context, n, ntok = run_agent(inputs, config, graph)
            output.append(
                {
                    "query": q,
                    "query_time": t,
                    "answer": res,
                    "ref_answer": row["answer"],
                    "context": context,
                    "num_llm_calls": n,
                    "total_tokens": ntok,   
                    "question_type": row["question_type"],
                    "static_or_dynamic": row["static_or_dynamic"],
                    "selected_tools": top_k_tools
                }
            )
            save_results(output_file, output)
        
    else:
        if args.use_all_tools:
            print('Using all tools....')
            tools = get_all_available_tools()
            tools = [search_knowledge_base] + tools # add retrieval tool
        else:
            print('Using only retrieval tool....')
            tools = [search_knowledge_base]
        graph = init_agent(args, tools)
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
            print(NUM_LLM_CALLS_BY_RETRIEVAL_TOOL)
            print(NUM_LLM_CALLS_BY_RETRIEVAL_TOOL+1)

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
            save_results(output_file, output)
            # n+=1
            # if n>=2:
            #     break
    
    save_results(output_file, output)
    save_as_csv(output_file)
