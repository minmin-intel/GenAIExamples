# pre-compute embedding of each tool
# compute embedding of user query
# compute similarity between user query and each tool
# return top k tools with highest similarity
from sentence_transformers import SentenceTransformer
import argparse
from tools.tools import get_all_available_tools
from utils import get_test_dataset, save_results
import os
import pandas as pd

def get_tools_descriptions():
    tools = get_all_available_tools()
    function_info = []
    for tool in tools:
        function_name = tool.name
        doc_string = tool.description
        # print("{}: {}".format(function_name, doc_string))
        if function_name != "search_knowledge_base":
            function_info.append("{}: {}".format(function_name, doc_string))
        # print("-"*50)
    return function_info

def sort_list(list1, list2):
    import numpy as np
    # Use numpy's argsort function to get the indices that would sort the second list
    idx = np.argsort(list2)# ascending order
    return np.array(list1)[idx].tolist()[::-1]# descending order

def get_topk_tools(topk, tools, similarities):
    sorted_tools = sort_list(tools, similarities)
    # print(sorted_tools)
    top_k_tools = sorted_tools[:topk]
    return [x.split(':')[0] for x in top_k_tools]
    

def select_tools_for_query(query, tools_embedding, model, topk, tools_descriptions):
    query_embedding = model.encode(query)
    similarities = model.similarity(query_embedding, tools_embedding).flatten() # 1D array
    top_k_tools = get_topk_tools(topk, tools_descriptions, similarities)
    # always provide search_knowledge_base tool
    top_k_tools.append("search_knowledge_base")
    return top_k_tools

def get_tool_with_name(tool_name, tools):
    # tools = get_all_available_tools()
    for tool in tools:
        if tool.name == tool_name:
            return tool
    return None

def get_selected_tools(top_k_tools):
    tools = get_all_available_tools()
    selected_tools = []
    for tool_name in top_k_tools:
        tool = get_tool_with_name(tool_name, tools)
        if tool is not None:
            selected_tools.append(tool)
    return selected_tools




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed_model", type=str, default="BAAI/bge-base-en-v1.5")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--query_file", type=str, default=None)
    args = parser.parse_args()

    tools_descriptions = get_tools_descriptions()

    model = SentenceTransformer(args.embed_model)

    tools_embeddings = model.encode(tools_descriptions)

    query=["how many songs have been released by barbra streisand since winning he/she won their first grammy?"]
    df = pd.DataFrame({"query": query})
    # df = get_test_dataset(args)
    output = []
    for _, row in df.iterrows():
        query = row["query"]
        top_k_tools = select_tools_for_query(query, tools_embeddings, model, args.k, tools_descriptions)
        output.append(
            {
                "query": query,
                "selected_tools": top_k_tools
            }
        )
    
    # filedir = "/localdisk/minminho/datasets/crag_results/"
    # output_file = "selected_tools_cossim.jsonl"
    # save_results(os.path.join(filedir, output_file), output)
    print(len(top_k_tools))
    print(get_selected_tools(top_k_tools))

   