# pre-compute embedding of each tool
# compute embedding of user query
# compute similarity between user query and each tool
# return top k tools with highest similarity
from sentence_transformers import SentenceTransformer
import argparse
from tools.tools import get_all_available_tools

def get_tools_descriptions():
    tools = get_all_available_tools()
    function_info = []
    for tool in tools:
        function_name = tool.name
        doc_string = tool.description
        # print("{}: {}".format(function_name, doc_string))
        function_info.append("{}: {}".format(function_name, doc_string))
        # print("-"*50)
    return function_info

def sort_list(list1, list2):
    import numpy as np
    # Use numpy's argsort function to get the indices that would sort the second list
    idx = np.argsort(list2)
    # Index the first list using the sorted indices and return the result as a numpy array
    return np.array(list1)[idx][::-1]

def get_topk_tools(topk, tools, similarities):
    sorted_tools = sort_list(tools, similarities)
    # print(sorted_tools)
    top_k_tools = sorted_tools.tolist()[:topk]
    return top_k_tools

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--embed_model", type=str, default="BAAI/bge-base-en-v1.5")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    tools_descriptions = get_tools_descriptions()

    model = SentenceTransformer(args.embed_model)

    tools_embeddings = model.encode(tools_descriptions)

    query=["how many songs have been released by barbra streisand since winning he/she won their first grammy?"]
    query_embedding = model.encode(query)
    # Compute cosine similarities
    similarities = model.similarity(query_embedding, tools_embeddings).flatten()

    for t, s in zip(tools_descriptions, similarities.argsort().tolist()):
        print("{}: {}".format(t, s))

    # Sort the tools by their cosine similarity in descending order
    # sorted_tools = sort_list(tools_descriptions, similarities)
    # print(sorted_tools)

    top_k_tools = get_topk_tools(args.k, tools_descriptions, similarities)
    print(top_k_tools)
    
   