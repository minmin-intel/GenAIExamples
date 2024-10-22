import pandas as pd
import os
import glob
from sentence_transformers import SentenceTransformer


def generate_column_descriptions(db_name):
    output = []
    decriptions_only = []
    working_dir = os.getenv("WORKDIR")
    assert working_dir is not None, "WORKDIR environment variable is not set."
    DESCRIPTION_FOLDER=os.path.join(working_dir, f"TAG-Bench/dev_folder/dev_databases/{db_name}/database_description/")
    table_files = glob.glob(os.path.join(DESCRIPTION_FOLDER, "*.csv"))
    for table_file in table_files:
        table_name = os.path.basename(table_file).split(".")[0]
        print("Table name: ", table_name)
        df = pd.read_csv(table_file)
        for _, row in df.iterrows():
            col_name = row["original_column_name"]
            # if pd.isnull(row["column_description"]) and (not pd.isnull(row["value_description"])):
            #     description = str(row["value_description"])
            # elif pd.isnull(row["value_description"]) and (not pd.isnull(row["column_description"])):
            #     description = str(row["column_description"])
            # elif (pd.isnull(row["column_description"])) and (pd.isnull(row["value_description"])):
            #     description = None
            # else:
            #     if row["column_description"].lower() in row["value_description"].lower():
            #         description = str(row["value_description"])
            #     elif row["value_description"].lower() in row["column_description"].lower():
            #         description = str(row["column_description"])
            #     else:
            #         description= str(row["column_description"]) + " "+ str(row["value_description"])
            if not pd.isnull(row["value_description"]):
                description = str(row["value_description"])
                # print(f"{col_name}: {description}")

            # if description is not None:    
                if description.lower() in col_name.lower():
                    print("Description {} is same as column name {}".format(description, col_name))
                    pass
                else:            
                    description = description.replace("\n", " ")
                    description = " ".join(description.split())
                    output.append(f"{table_name}.{col_name}: {description}\n")
                    decriptions_only.append(description)
    # print("Output:\n", output)
    return output, decriptions_only

def sort_list(list1, list2):
    import numpy as np
    # Use numpy's argsort function to get the indices that would sort the second list
    idx = np.argsort(list2)# ascending order
    return np.array(list1)[idx].tolist()[::-1], np.array(list2)[idx].tolist()[::-1]# descending order

def get_topk_cols(topk, cols_descriptions, similarities):
    sorted_cols, similarities = sort_list(cols_descriptions, similarities)
    top_k_cols = sorted_cols[:topk]
    output = []
    for col, sim in zip(top_k_cols, similarities[:topk]):
        print(f"{col}: {sim}")
        if sim > 0.45:
            output.append(col)
    return output #top_k_cols


def pick_hints(query, model, column_embeddings, complete_descriptions, topk=5):
    # use similarity to get the topk columns
    # model = SentenceTransformer('BAAI/bge-base-en-v1.5')

    query_embedding = model.encode(query, convert_to_tensor=True)
    similarities = model.similarity(query_embedding, column_embeddings).flatten()

    topk_cols_descriptions = get_topk_cols(topk, complete_descriptions, similarities)

    # hint = ""
    # for col in topk_cols_descriptions:
    #     hint += (col +'\n')
    # return hint
    return topk_cols_descriptions

def generate_hints(db_name):
    # use llm to generate hints
    complete_descriptions, cols_descriptions = generate_column_descriptions(db_name)

    hints = ""
    for col in complete_descriptions:
        hints += (col +'\n')

    # print("ALL HINTS: ", hints)
    # print("================= END OF ALL HINTS ================")
    return hints


def make_documents_from_column_descriptions(complete_descriptions):
    from langchain_core.documents import Document
    documents = []
    for description in complete_descriptions:
        temp = description.split(":")
        content = temp[1]
        meta = {"table_col": temp[0]}
        documents.append(Document(page_content=content, metadata=meta))
    return documents

def pick_hints_bm25(retriever, query):
    docs = retriever.invoke(query)
    hints = ""
    for doc in docs:
        temp = doc.metadata["table_col"] + ": " + doc.page_content #doc.page_content #
        hints += temp + "\n"
    return hints
    
def generate_hints_given_keywords_list(query, keywords, model, column_embeddings, complete_descriptions, topk=3):
    hints = []
    for keyword in keywords:
        hint = pick_hints(keyword, model, column_embeddings, complete_descriptions, topk=topk)
        print("Query: ", keyword)
        print("Hint:\n", hint)
        print("--"*20)
        hints.extend(hint)
    hints_set = set(hints)
    hints_list = list(hints_set)
    print("# hints: ", len(hints_list))
    # run similarity against query and pick top-5
    hints_no_table_name = [hint.split(":")[1] for hint in hints_list]
    hints_embeddings = model.encode(hints_list)
    query_embedding = model.encode(query, convert_to_tensor=True)
    similarities = model.similarity(query_embedding, hints_embeddings).flatten()
    final_hints_list = get_topk_cols(5, hints_list, similarities)
    print("Final hints: ", len(final_hints_list))
    final_hints = ""
    for hint in final_hints_list:
        final_hints += hint + "\n"
    return final_hints

if __name__ == "__main__":
    db_name = "california_schools"
    complete_descriptions, cols_descriptions = generate_column_descriptions(db_name)

    # # bm25
    # from langchain_community.retrievers import BM25Retriever
    # documents = make_documents_from_column_descriptions(complete_descriptions)
    # topk=5
    # bm25_retriever = BM25Retriever.from_documents(documents, k = topk)
    # # query = "Summarize the qualities of the schools with an average score in Math under 600 in the SAT test and are exclusively virtual."
    # query = "continuation schools" #eligible free rates, overall affordability
    # hints = pick_hints_bm25(bm25_retriever, query)
    # print(hints)

    # # similarity
    model = SentenceTransformer('BAAI/bge-base-en-v1.5')
    column_embeddings = model.encode(cols_descriptions)
    # query = "Summarize the qualities of the schools with an average score in Math under 600 in the SAT test and are exclusively virtual."
    # query = "continuation schools" #eligible free rates, overall affordability
    # query_list = ["continuation schools", "eligible free rates", "overall affordability"]
    # hints = []
    # for query in query_list:
    #     hint = pick_hints(query, column_embeddings, complete_descriptions, topk=3)
    #     print("Query: ", query)
    #     print("Hint:\n", hint)
    #     print("=="*20)
    #     hints.extend(hint)
    # hints_set = set(hints)
    # for hint in hints_set:
    #     print('Final hint:\n', hint)
    working_dir = os.getenv("WORKDIR")
    # df = pd.read_csv(f"{working_dir}/TAG-Bench/query_by_db/query_california_schools.csv")
    df = pd.read_csv(f"{working_dir}/sql_agent_output/keywords.csv")
    hint_cols = []
    for _, row in df.iterrows():
        query = row["Query"]
        # hint = pick_hints(query, column_embeddings, complete_descriptions)
        # print("Query: ", query)
        keywords = row["keywords"]
        keywords = keywords.split(",")
        hint = generate_hints_given_keywords_list(query, keywords, model, column_embeddings, complete_descriptions, topk=3)
        print("Hint: ", hint)
        print("=="*20)
        hint_cols.append(hint)
    df["hints"] = hint_cols
    df.to_csv(f"{working_dir}/sql_agent_output/keywords_hints_llam3.1-70b_noschema.csv", index=False)