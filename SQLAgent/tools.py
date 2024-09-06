import pandas as pd
import os

DESCRIPTION_FOLDER="/localdisk/minminho/TAG-Bench/dev_folder/dev_databases/california_schools/database_description/"

def get_column_descriptions(df):
    output = "Column: Description\n"
    for _, row in df.iterrows():
        col_name = row["original_column_name"]
        if pd.isnull(row["column_description"]) and (not pd.isnull(row["value_description"])):
            description = str(row["value_description"])
        elif pd.isnull(row["value_description"]) and (not pd.isnull(row["column_description"])):
            description = str(row["column_description"])
        elif (pd.isnull(row["column_description"])) and (pd.isnull(row["value_description"])):
            description = "no description"
        else:
            description= str(row["column_description"]) + " "+ str(row["value_description"])
        description = description.replace("\n", " ")
        description = " ".join(description.split())
        output += f"{col_name}: {description}\n"
    return output


def get_table_info(table_name:str):
    filename = os.path.join(DESCRIPTION_FOLDER, f"{table_name}.csv")  
    df = pd.read_csv(filename)
    return get_column_descriptions(df)

# if __name__ == "__main__":
#     print(get_table_info("schools"))
#     print("====================================")
#     print(get_table_info("satscores"))
#     print("====================================")
#     print(get_table_info("frpm"))
