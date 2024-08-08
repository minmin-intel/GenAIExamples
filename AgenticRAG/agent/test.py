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
NUM_TOKENS_BY_RETRIEVAL_TOOL = 0

def init_agent(args, tools):
    if "react" in args.agent_type:
        from prompt import REACT_SYS_MESSAGE_V2
        if args.use_hf_tgi:
            model = setup_hf_tgi_client(args)
        else:
            model = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0)
        graph = create_react_agent(model, tools = tools, state_modifier=REACT_SYS_MESSAGE_V2)
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
                total_tokens = 500 #rough estimate
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
            # context = get_last_tool_message(s["messages"])
            response = s['output']
        else:
            # print('output key not in state')
            response = s["messages"][-1].content

        context = get_trace(s["messages"])
        print('***Final output:\n{} \n****End of output****'.format(response))
        # print('***Context:\n{} \n****End of context****'.format(context))
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
    parser.add_argument("--agent_type", type=str, default="react_tool_selection", help="react, doc_grader, react_tool_selection")
    parser.add_argument("--use_all_tools", type=bool, default=False)
    parser.add_argument("--use_advanced_retrieval", type=bool, default=False)
    parser.add_argument("--use_docgrader_as_tool", type=bool, default=True)
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
    parser.add_argument("--query_file", type=str, default="/home/user/datasets/crag_qas/crag_20_answerable_queries.csv", help="query file")
    parser.add_argument("--quick_test", type=bool, default=False)
    args = parser.parse_args()
    print(args)

    RECURSION_LIMIT = 10
    config = {"recursion_limit": RECURSION_LIMIT}
    output = []
    output_dir = "/home/user/datasets/crag_results/"
    filename = "crag_20queries_react_docgradertool_top5apis_v2sysm_gpt4omini.jsonl"
    output_file = output_dir + filename

    if args.quick_test:
        query= [
            # "how many reading and leeds festivals has the band foo fighters headlined?",
            # "how many songs has the band the beatles released that have been recorded at abbey road studios?",
            "what's the most recent album from the founder of ysl records?",
            # "when did dolly parton's song, blown away, come out?"
            # "what song topped the billboard chart on 2004-02-04?",
            # "what grammy award did edgar barrera win this year?",
            "who has had more number one hits on the us billboard hot 100 chart, michael jackson or elvis presley?",
        ]
        query_time=[
            "03/21/2024, 23:37:29 PT", 
            "03/21/2024, 23:37:29 PT",
            # "03/21/2024, 23:37:29 PT",
            # "03/21/2024, 23:37:29 PT",
            ]
        df = pd.DataFrame({"query": query, "query_time": query_time})
    else:
        df = get_test_dataset(args)


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
                "num_grade":0,
                "num_tokens":0,
            }
            
            for s in retrieval_agent.stream(inputs, config={"recursion_limit": 10}, stream_mode="values"):
                for k, v in s.items():
                    if k in ["num_retrieve", "num_rewrites", "num_grade", "num_tokens"]:
                        print("**RETRIEVAL TOOL** {}:\n{}".format(k,v))

            context = s["relevant"]
            print('**Retrieval Tool output: ', context)
            global NUM_LLM_CALLS_BY_RETRIEVAL_TOOL
            global NUM_TOKENS_BY_RETRIEVAL_TOOL
            NUM_LLM_CALLS_BY_RETRIEVAL_TOOL = (s["num_rewrites"]+s['num_grade'])
            NUM_TOKENS_BY_RETRIEVAL_TOOL = s["num_tokens"]
            if context:    
                return context
            else:
                ret = "No relevant information found in the knowledge base."
                print("****"+ret)
                return ret            
    elif args.use_docgrader_as_tool:
        from langchain_core.tools import tool
        from agent import RAGAgentDocGraderV1
        from tools.tools import retrieve_from_knowledge_base
        retrieval_agent = RAGAgentDocGraderV1(args, [retrieve_from_knowledge_base]).app
        @tool
        def search_knowledge_base(query:str)->str:
            '''Search knowledge base for a given query. Returns text related to the query.'''
            global NUM_LLM_CALLS_BY_RETRIEVAL_TOOL
            global NUM_TOKENS_BY_RETRIEVAL_TOOL
            inputs = {
                "messages": [("user", query)],
                "query_time": "",
            }
            try:
                for s in retrieval_agent.stream(inputs, config={"recursion_limit": 10}, stream_mode="values"):
                    for k, v in s.items():
                        if k != "messages":
                            print("**RETRIEVAL TOOL** {}:\n{}".format(k,v))
                context = s["output"]

                # get statistics
                NUM_LLM_CALLS_BY_RETRIEVAL_TOOL += get_num_llm_calls(s["messages"])
                NUM_TOKENS_BY_RETRIEVAL_TOOL += get_total_tokens(s["messages"])   

                return context
            except Exception as e:
                ret = "No relevant information found in the knowledge base."
                print("****Exception in DocGrader tool: ", e)
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
            print('****Selected APIs: ', top_k_tools)
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
            print("LLM calls by retrieval tool: ", NUM_LLM_CALLS_BY_RETRIEVAL_TOOL)
            print("Total tokens by retrieval tool: ", NUM_TOKENS_BY_RETRIEVAL_TOOL)
            print("Total LLM calls: ", n+NUM_LLM_CALLS_BY_RETRIEVAL_TOOL)
            print("Total tokens: ", ntok+NUM_TOKENS_BY_RETRIEVAL_TOOL)
            print("==**"*100)
            output.append(
                {
                    "query": q,
                    "query_time": t,
                    "ref_answer": row["answer"],
                    "answer": res,
                    "context": context,
                    "num_llm_calls": n+NUM_LLM_CALLS_BY_RETRIEVAL_TOOL,
                    "total_tokens": ntok+NUM_TOKENS_BY_RETRIEVAL_TOOL,  
                    "question_type": row["question_type"],
                    "static_or_dynamic": row["static_or_dynamic"],
                    "selected_tools": top_k_tools
                }
            )
            save_results(output_file, output)
            NUM_TOKENS_BY_RETRIEVAL_TOOL = 0
            NUM_LLM_CALLS_BY_RETRIEVAL_TOOL = 0
        
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
            print("LLM calls by retrieval tool: ", NUM_LLM_CALLS_BY_RETRIEVAL_TOOL)
            print("Total tokens by retrieval tool: ", NUM_TOKENS_BY_RETRIEVAL_TOOL)
            print("Total LLM calls: ", n+NUM_LLM_CALLS_BY_RETRIEVAL_TOOL)
            print("Total tokens: ", ntok+NUM_TOKENS_BY_RETRIEVAL_TOOL)
            print("==**"*100)

            output.append(
                {
                    "query": q,
                    "query_time": t,
                    "ref_answer": row["answer"],
                    "answer": res,
                    "context": context,
                    "num_llm_calls": n+NUM_LLM_CALLS_BY_RETRIEVAL_TOOL,
                    "total_tokens": ntok+NUM_TOKENS_BY_RETRIEVAL_TOOL,
                    "question_type": row["question_type"],
                    "static_or_dynamic": row["static_or_dynamic"],
                }
            )
            save_results(output_file, output)
            # n+=1
            # if n>=2:
            #     break
            NUM_TOKENS_BY_RETRIEVAL_TOOL = 0
            NUM_LLM_CALLS_BY_RETRIEVAL_TOOL = 0
    
    save_results(output_file, output)
    save_as_csv(output_file)
