import pandas as pd
import os
from typing import Type
# from langchain_core.pydantic_v1 import BaseModel, Field
# from langchain_core.tools import BaseTool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.tools import tool
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool, ListSQLDatabaseTool, QuerySQLCheckerTool, InfoSQLDatabaseTool

working_dir = os.getenv("WORKDIR")
DESCRIPTION_FOLDER=os.path.join(working_dir, "TAG-Bench/dev_folder/dev_databases/california_schools/database_description/")

def get_column_descriptions(df):
    output = ""
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

@tool
def get_table_info(table_names:str)->str:
    '''Get the names and descriptions of all the columns in a table.
    Args:
        table_names: A comma-separated list of the table names for which to return the schema. Example input: 'table1, table2, table3'
    '''
    table_names = table_names.split(",")
    output = ""
    for table_name in table_names:
        filename = os.path.join(DESCRIPTION_FOLDER, f"{table_name.strip()}.csv")
        df = pd.read_csv(filename)
        des = get_column_descriptions(df)
        output += f"Table: {table_name}\n----------\n{des}\n\n"
    return output

@tool
def get_column_description(table_name:str, column_name:str)->str:
    '''Get the descriptions of the categorical values of a column.
    Args:
        table_name: The name of the table.
        column_name: The name of the column.
    '''
    filename = os.path.join(DESCRIPTION_FOLDER, f"{table_name}.csv")
    df = pd.read_csv(filename)
    df = df[df["original_column_name"]==column_name]
    return get_column_descriptions(df)


def get_database(path):
    uri= "sqlite:///{path}".format(path=path)
    db = SQLDatabase.from_uri(uri)
    print(db.dialect)
    print(db.get_usable_table_names())
    return db

# @tool
# def search_web(query: str)->str:
#     '''Search the web for information not contained in databases.'''
#     from langchain_community.tools import DuckDuckGoSearchRun
#     search = DuckDuckGoSearchRun()
#     return search.invoke(query)

@tool
def search_web(query: str)->str:
    '''Search the web for information not contained in databases.'''
    from tavily import TavilyClient
    import os
    TAVILYKEY=os.getenv("TAVILY_API_KEY")
    tavily = TavilyClient(api_key=TAVILYKEY)
    search_params = {
        "search_depth":"advanced",
        "max_results":3,
        "include_answer":True
    }

    ret_text = ""
    
    try:
        print('Query:\n', query)
        res = tavily.search(query=query, **search_params)
        answer = res['answer']
        print('Answer:\n', answer)
        # query = answer
        ret_text = answer
    except Exception as e:    
        ret_text = "Exception occurred during search: {}".format(str(e))
        print(str(e))

    return ret_text


def get_tools(args, llm):
    db = get_database(args.path)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()
    # print("SQL toolkit tools: ", tools)
    # sql_tools = []
    # for tool in tools:
    #     if isinstance(tool, InfoSQLDatabaseTool):
    #         pass
    #     else:
    #         sql_tools.append(tool)
    # # print("SQL tools: ", sql_tools)
    # final_tools = sql_tools+[get_table_info]
    # print("Tools for agent to use:\n", final_tools)
    # return final_tools
    tools = tools + [get_column_description, search_web]
    return tools



# def query_fixer(query):


def get_tools_sql_agent(args):
    working_dir = os.getenv("WORKDIR")
    db_name = args.db_name
    DBPATH=f"{working_dir}/TAG-Bench/dev_folder/dev_databases/{db_name}/{db_name}.sqlite"
    uri= "sqlite:///{path}".format(path=DBPATH)
    db = SQLDatabase.from_uri(uri)
    query_sql_database_tool_description = (
            "Input to this tool is a detailed and correct SQL query, output is a "
            "result from the database. If the query is not correct, an error message "
            "will be returned. If an error is returned, rewrite the query, check the "
            "query, and try again. "
        )
    db_query_tool = QuerySQLDataBaseTool(db=db, description=query_sql_database_tool_description)
    return [db_query_tool, search_web]



# if __name__ == "__main__":
#     # print(get_table_info("schools, satscores, frpm"))
#     print(get_column_description("schools", "Virtual"))
    # print("====================================")
    # print(get_table_info("satscores"))
    # print("====================================")
    # print(get_table_info("frpm"))
