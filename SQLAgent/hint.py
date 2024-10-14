import pandas as pd
import os
import glob
from sentence_transformers import SentenceTransformer, util





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
            if pd.isnull(row["column_description"]) and (not pd.isnull(row["value_description"])):
                description = str(row["value_description"])
            elif pd.isnull(row["value_description"]) and (not pd.isnull(row["column_description"])):
                description = str(row["column_description"])
            elif (pd.isnull(row["column_description"])) and (pd.isnull(row["value_description"])):
                description = None
            else:
                if row["column_description"].lower() in row["value_description"].lower():
                    description = str(row["value_description"])
                elif row["value_description"].lower() in row["column_description"].lower():
                    description = str(row["column_description"])
                else:
                    description= str(row["column_description"]) + " "+ str(row["value_description"])

            if description is not None:
                description = description.replace("\n", " ")
                description = " ".join(description.split())
                output.append(f"{table_name}.{col_name}: {description}\n")
                decriptions_only.append(description)
    # print("Output:\n", output)
    return output, descriptions_only

def sort_list(list1, list2):
    import numpy as np
    # Use numpy's argsort function to get the indices that would sort the second list
    idx = np.argsort(list2)# ascending order
    return np.array(list1)[idx].tolist()[::-1]# descending order

def get_topk_cols(topk, cols_descriptions, similarities):
    sorted_cols = sort_list(cols_descriptions, similarities)
    top_k_cols = sorted_cols[:topk]
    return top_k_cols


def generate_hints(query, column_embeddings, cols_descriptions, complete_descriptions, topk=5):
    model = SentenceTransformer('BAAI/bge-base-en-v1.5')

    query_embedding = model.encode(query, convert_to_tensor=True)
    similarities = model.similarity(query_embedding, column_embeddings).flatten()

    topk_cols_descriptions = get_topk_cols(topk, cols_descriptions, similarities)

    hint = ""
    for col in topk_cols_descriptions:
        hint += (col +'\n')
    return hint

if __name__ == "__main__":
    db_name = "california_schools"
    model = SentenceTransformer('BAAI/bge-base-en-v1.5')

    complete_descriptions, cols_descriptions = generate_column_descriptions(db_name)
    column_embeddings = model.encode(cols_descriptions)
    # query = "Of the cities containing exclusively virtual schools which are the top 3 safest places to live?"
    # hint = generate_hints(query, column_embeddings, cols_descriptions)
    # print(hint)
    working_dir = os.getenv("WORKDIR")
    df = pd.read_csv(f"{working_dir}/TAG-Bench/query_by_db/query_california_schools.csv")
    hint_cols = []
    for _, row in df.iterrows():
        query = row["Query"]
        hint = generate_hints(query, column_embeddings, cols_descriptions)
        print("Query: ", query)
        print("Hint: ", hint)
        print("=="*20)
        hint_cols.append(hint)
    df["hints"] = hint_cols
    df.to_csv(f"{working_dir}/sql_agent_output/query_california_schools_with_hints.csv", index=False)