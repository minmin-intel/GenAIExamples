import uuid
import json
from langchain_core.messages.tool import ToolCall
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage


def remove_repeated_tool_calls(tool_calls, messages):
    """
    Remove repeated tool calls in the messages.
    tool_calls: list of tool calls: ToolCall(name=tool_name, args=tool_args, id=tcid)
    messages: list of messages: AIMessage, ToolMessage, HumanMessage
    """
    # first get all the previous tool calls in messages
    previous_tool_calls = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls and m.content != "Repeated previous steps.":
            for tc in m.tool_calls:
                previous_tool_calls.append({"tool": tc["name"], "args": tc["args"]})
    
    unique_tool_calls = []
    for tc in tool_calls:
        if {"tool": tc["name"], "args": tc["args"]} not in previous_tool_calls:
            unique_tool_calls.append(tc)

    return unique_tool_calls


def parse_sql_query(line):
    # sql_db_query - {'query': "SELECT T1…”}
    temp = line.split("sql_db_query - ")[-1]
    try:
        query = json.loads(temp)["query"]
    except:
        query = None
    return query

def get_sql_query_from_output(output):
    """
    get the content of the sql query from the output like below:
    ```sql
    SELECT * 
    FROM schools 
    WHERE CDSCode IN ('12345', '67890');
    ```
    There may be multiple such instances. Only get the last one.
    """
    if "```sql" not in output:
        return None
    else:
        query = output.split("```sql")[-1].split("```")[0]
        return query

def get_tool_calls_other_than_sql(text):
    """
    get the tool calls other than sql_db_query
    """
    tool_calls = []
    text = text.replace("assistant", "")
    json_lines = text.split("\n")
    # only get the unique lines
    json_lines = list(set(json_lines))
    for line in json_lines:
        if "TOOL CALL:" in line:
            if "sql_db_query" not in line:
                line = line.replace("TOOL CALL:", "")
                if "assistant" in line:
                    line = line.replace("assistant", "")
                if "\\" in line:
                    line = line.replace("\\", "")
                try:
                    parsed_line = json.loads(line)
                    if isinstance(parsed_line, dict):
                        if "tool" in parsed_line:
                            tool_calls.append(parsed_line)
                
                except:
                    pass
    return tool_calls

# v5: answer last
# v6: answer first
# v7: multiple tool calls together
def parse_tool_calls(text):
    # try to get tool call in format: TOOL CALL: {"tool": "sql_db_query", "args": {"query": "SELECT ..."}}
    tool_calls = get_tool_calls_other_than_sql(text)
    sql_query = get_sql_query_from_output(text)
    if sql_query:
        sql_tool_call = [{"tool": "sql_db_query", "args": {"query": sql_query}}]
        tool_calls.extend(sql_tool_call)
    return tool_calls

def parse_answer(text):
    lines = text.split("\n")
    for line in lines:
        if "FINAL ANSWER:" in line.upper():
            line = line.replace("FINAL ANSWER:", "")
            line = line.replace("assistant", "")
            try:
                parsed_line = json.loads(line)
                if isinstance(parsed_line, dict):
                    if "answer" in parsed_line:
                        return parsed_line
            except:
                return None
    return None

ANSWER_PARSER_PROMPT_v1 = """\
Review the output from an SQL agent and determine if a correct answer has been provided and grounded on real data. 

Say "yes" when all the following conditions are met:
1. The answer is complete and does not require additional steps to be taken.
2. The answer does not have placeholders that need to be filled in.
3. The answer is Not based on agent's assumptions or guesses or imaginations.
4. The agent has acquired data from database and its execution history is Not empty.

If the conditions above are not met, say "no".

Here is the output from the SQL agent:
{output}
======================
Here is the agent execution history:
{history}
======================

Has a final answer been provided based on real data? Analyze the agent output and make your judgement "yes" or "no".
"""

ANSWER_PARSER_PROMPT = """\
Review the output from an SQL agent and determine if a correct answer has been provided and grounded on real data. 

Say "yes" when all the following conditions are met:
1. The answer is complete and does not require additional steps to be taken.
2. The answer does not have placeholders that need to be filled in.
3. The agent has acquired data from database and its execution history is Not empty.
4. The answer is based on data.

If the conditions above are not met, say "no".

Here is the output from the SQL agent:
{output}
======================
Here is the agent execution history:
{history}
======================

Has a final answer been provided based on real data? Analyze the agent output and make your judgement "yes" or "no".
"""

def parse_answer_with_llm(text, history, chat_model):
    if "FINAL ANSWER:" in text.upper():
        if history == "":
            history = "The agent execution history is empty."
        # else:
        #     history = "Agent has acquired data from database."
        prompt = ANSWER_PARSER_PROMPT.format(output=text, history=history)
        response = chat_model.invoke(prompt).content
        print("@@@ Answer parser response: ", response)
        # if "yes" in response.lower():
        #     return text.split("FINAL ANSWER:")[-1]
        # else:
        #     return None
        temp = response[:5]
        if "yes" in temp.lower():
            return text.split("FINAL ANSWER:")[-1]
        else:
            return None
    else:
        return None


class LlamaOutputParser:
    def __init__(self, chat_model):
        self.chat_model = chat_model

    def parse(self, text: str, history: str):
        print("@@@ Raw output from llm:\n", text)
        answer = parse_answer_with_llm(text, history, self.chat_model)
        if answer:
            print("Final answer exists.")
            return answer
        else:
            tool_calls = parse_tool_calls(text)
            if tool_calls:
                return tool_calls
            else:
                return text
        
SQL_QUERY_PARSER_PROMPT = """\
Review the set of SQL queries below. Pick the query that is most likely to provide the correct answer to the user question. 

SQL Queries:
{queries}

User Question:
{question}

Write down the number of the SQL query that you think is the most appropriate.
"""

SQL_QUERY_FIXER_PROMPT = """\
You are an SQL database expert tasked with reviewing a SQL query written by an agent. 
**Procedure:**
1. Review Database Schema:
- Examine the table creation statements to understand the database structure.
2. Review the Hint provided.
- Use the provided hints to understand the domain knowledge relevant to the query.
3. Check against the following common errors:
- Failure to exclude null values, syntax errors, incorrect table references, incorrect column references, logical mistakes.
4. Check if aggregation should be used:
- Read the user question, and determine if user is asking for specific instances or aggregated info. If aggregation is needed, check if the original SQL query has used appropriate functions like COUNT and SUM.
5. Correct the Query only when Necessary:
- If issues were identified, modify the SQL query to address the identified issues, ensuring it correctly fetches the requested data according to the database schema and query requirements.
- Note: Some user questions can only be answered partially with the database. This is OK. The agent will use other tools in subsequent steps to get additional info. Your goal is to write the correct SQL query to fetch the relevant data that is available in the database.
- Only use the tables provided in the database schema in your corrected query. Do not join tables that are not present in the schema. Do not create any new tables.

======= Your task =======
**************************
Table creation statements
{DATABASE_SCHEMA}
**************************
Hint:
{HINT}
**************************
The SQL query to review:
{QUERY}
**************************
User question:
{QUESTION}
**************************

Now analyze the SQL query step by step. Present your reasonings. 

If you identified issues in the original query, write down the corrected SQL query in the format below:
```sql
SELECT column1, column2, ...
``` 

If the original SQL query is correct, just say the query is correct.
"""

SQL_QUERY_FIXER_PROMPT_with_result = """\
You are an SQL database expert tasked with reviewing a SQL query. 
**Procedure:**
1. Review Database Schema:
- Examine the table creation statements to understand the database structure.
2. Review the Hint provided.
- Use the provided hints to understand the domain knowledge relevant to the query.
3. Analyze Query Requirements:
- User Question: Consider what information the query is supposed to retrieve. Decide if aggregation like COUNT or SUM is needed.
- Executed SQL Query: Review the SQL query that was previously executed.
- Execution Result: Analyze the outcome of the executed query. Think carefully if the result makes sense. 
4. Check against the following common errors:
- Failure to exclude null values, syntax errors, incorrect table references, incorrect column references, logical mistakes.
5. Correct the Query only when Necessary:
- If issues were identified, modify the SQL query to address the identified issues, ensuring it correctly fetches the requested data according to the database schema and query requirements.
- Note: Some user questions can only be answered partially with the database. This is OK. The agent will use other tools in subsequent steps to get additional info. Your goal is to write the correct SQL query to fetch the relevant data that is available in the database.
- Only use the tables provided in the database schema in your corrected query. Do not join tables that are not present in the schema. Do not create any new tables.

======= Your task =======
**************************
Table creation statements
{DATABASE_SCHEMA}
**************************
Hint:
{HINT}
**************************
User Question:
{QUESTION}
**************************
The SQL query executed was:
{QUERY}
**************************
The execution result:
{RESULT}
**************************

Now analyze the SQL query step by step. Present your reasonings. 

If you identified issues in the original query, write down the corrected SQL query in the format below:
```sql
SELECT column1, column2, ...
``` 

If the original SQL query is correct, just say the query is correct.
"""

def get_all_sql_queries(text):
    queries = []
    if "```sql" in text:
        temp = text.split("```sql")
        for t in temp:
            if "```" in t:
                query = t.split("```")[0]
                if "SELECT" in query.upper() and "TOOL CALL" not in query.upper():
                    queries.append(query)

    return queries

def format_sql_queries(queries):
    formatted_queries = ""
    for i, q in enumerate(queries):
        formatted_queries += f"{i+1}.\n{q}\n"
    return formatted_queries

def get_the_last_sql_query(text):
    queries = get_all_sql_queries(text)
    if queries:
        return queries[-1]
    else:
        return None
    

def parse_and_fix_sql_query(text, chat_model, db_schema, hint, question):
    chosen_query = get_the_last_sql_query(text)
    if chosen_query:
        prompt = SQL_QUERY_FIXER_PROMPT.format(DATABASE_SCHEMA=db_schema, HINT=hint, QUERY=chosen_query, QUESTION=question)
        response = chat_model.invoke(prompt).content
        print("@@@ SQL query fixer response: ", response)
        if "query is correct" in response.lower():
            return chosen_query
        else:
            # parse the fixed query
            fixed_query = get_the_last_sql_query(response)
            return fixed_query           
    else:
        return None

def check_query_if_executed_and_result(query, messages):
    # get previous sql_db_query tool calls
    previous_tool_calls = []
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            for tc in m.tool_calls:
                if tc["name"] == "sql_db_query":
                    previous_tool_calls.append(tc)
    for tc in previous_tool_calls:
        if query == tc["args"]["query"]:
            return get_tool_output(messages, tc["id"])
        
    return None


def parse_and_fix_sql_query_v2(text, chat_model, db_schema, hint, question, messages):
    chosen_query = get_the_last_sql_query(text)
    if chosen_query:
        # check if the query has been executed before
        # if yes, pass execution result to the fixer
        # if not, pass the query to the fixer
        result = check_query_if_executed_and_result(chosen_query, messages)
        if result:
            prompt = SQL_QUERY_FIXER_PROMPT_with_result.format(DATABASE_SCHEMA=db_schema, HINT=hint, QUERY=chosen_query, QUESTION=question, RESULT=result)
        else:
            prompt = SQL_QUERY_FIXER_PROMPT.format(DATABASE_SCHEMA=db_schema, HINT=hint, QUERY=chosen_query, QUESTION=question)
        
        response = chat_model.invoke(prompt).content
        print("@@@ SQL query fixer response: ", response)
        if "query is correct" in response.lower():
            return chosen_query
        else:
            # parse the fixed query
            fixed_query = get_the_last_sql_query(response)
            return fixed_query           
    else:
        return None

class LlamaOutputParserAndQueryFixer:
    def __init__(self, chat_model):
        self.chat_model = chat_model

    def parse(self, text: str, history: str, db_schema: str, hint: str, question: str, messages: list):
        print("@@@ Raw output from llm:\n", text)
        answer = parse_answer_with_llm(text, history, self.chat_model)
        if answer:
            print("Final answer exists.")
            return answer
        else:
            tool_calls = get_tool_calls_other_than_sql(text)
            sql_query = parse_and_fix_sql_query_v2(text, self.chat_model, db_schema, hint, question, messages)
            if sql_query:
                sql_tool_call = [{"tool": "sql_db_query", "args": {"query": sql_query}}]
                tool_calls.extend(sql_tool_call)
            if tool_calls:
                return tool_calls
            else:
                return text
            
            

            
class LlamaOutputParserV7(BaseOutputParser):
    """
    Assumptions:
    1. the final sql query in raw llm output is the query that agent wants to execute.
    2. If FINAL ANSWER is in text, we consider it to be final.
    3. If other tools like search_web, etc. are called together with sql query tool, the other tools should take priority over sql_db_query, to first gather related info first.
    """
    def parse(self, text: str):
        print("@@@ Raw output from llm:\n", text)
        answer_dict = parse_answer(text)
        if answer_dict:
            return [answer_dict]
        else:
            tool_calls = parse_tool_calls(text)
            if tool_calls:
                return tool_calls
            else:
                return text
        

class LlamaOutputParserV6(BaseOutputParser):
    """
    Assumptions:
    1. the final sql query in raw llm output is the query that agent wants to execute.
    2. If FINAL ANSWER is in text, we consider it to be final.
    3. If other tools like search_web, etc. are called together with sql query tool, the other tools should take priority over sql_db_query, to first gather related info first.
    """
    def parse(self, text: str):
        print("@@@ Raw output from llm:\n", text)
        if "FINAL ANSWER:" in text.upper():
            answer = text.split("FINAL ANSWER:")[-1]
            if answer:
                return [{"answer": answer}]
            else:
                return parse_tool_calls(text)
        else:
            return parse_tool_calls(text)
                

class LlamaOutputParserV3(BaseOutputParser):
    """
    Assumptions:
    1. the final sql query in raw llm output is the query that agent wants to execute.
    2. If FINAL ANSWER is in text, but there are tool calls, we assume agent needs to work more and the answer is not the final one.
    3. If other tools like search_web, etc. are called together with sql query tool, the other tools should take priority over sql_db_query, to first gather related info first.
    """
    def parse(self, text: str):
        print("@@@ Raw output from llm:\n", text)
        # try to get tool call in format: TOOL CALL: {"tool": "sql_db_query", "args": {"query": "SELECT ..."}}
        tool_calls = get_tool_calls_other_than_sql(text)
        if tool_calls:
            return tool_calls
        else:
            # try to get sql query
            sql_query = get_sql_query_from_output(text)
            if sql_query:
                return [{"tool": "sql_db_query", "args": {"query": sql_query}}]
            else:
                if "FINAL ANSWER:" in text.upper():
                    return [{"answer": text.split("FINAL ANSWER:")[-1]}]
                else:
                    return text
        


class LlamaOutputParserV1(BaseOutputParser):
    def parse(self, text: str):
        print("@@@ Raw output from llm:\n", text)
        json_lines = text.split("\n")
        output = []
        for line in json_lines:
            
            if "TOOL CALL:" in line:
                line = line.replace("TOOL CALL:", "")
                if "sql_db_query" in line:
                    query = parse_sql_query(line)
                    if query:
                        output.append({"tool": "sql_db_query", "args": {"query": query}})
            if "FINAL ANSWER:" in line:
                line = line.replace("FINAL ANSWER:", "")
                # output.append({"answer": line})
            if "assistant" in line:
                line = line.replace("assistant", "")
            if "\\" in line:
                line = line.replace("\\", "")
            try:
                parsed_line = json.loads(line)
                if isinstance(parsed_line, dict):
                    if "tool" in parsed_line or "answer" in parsed_line:
                        print("parsed line: ", parsed_line)
                        output.append(parsed_line)
                    else:
                        print("Parsed line is not a tool call or answer: ", parsed_line)
            except Exception as e:
                # print("Error parsing line: ", e)
                pass
        if output:
            return output
        else:
            if "FINAL ANSWER:" in text:
                output.append({"answer": text.split("FINAL ANSWER:")[-1]})
                return output
            else:
                # try parsing sql
                sql_query = get_sql_query_from_output(text)
                if sql_query:
                    output.append({"tool": "sql_db_query", "args": {"query": sql_query}})
                    return output
                else:
                    return text
        

def convert_json_to_tool_call(json_str):
    tool_name = json_str["tool"]
    tool_args = json_str["args"]
    tcid = str(uuid.uuid4()) 
    tool_call = ToolCall(name=tool_name, args=tool_args, id=tcid)
    return tool_call


def get_tool_output(messages, id):
    tool_output = ""
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            if msg.tool_call_id == id:
                tool_output = msg.content
                tool_output = tool_output[:1000] # limit to 1000 characters
                break
    return tool_output


HISTORY_SUMMARY_PROMPT = """\
Your task is to summarize the steps that have been taken by an SQL agent.
Capture the most important information contained the steps so that the agent can quickly understand the progress made so far and any corrections that need to be made.

Steps taken:
{steps}

Your summary:
"""

def assemble_history_v1(messages):
    """
    messages: AI, TOOL, AI, TOOL, etc.
    """
    query_history = ""
    breaker = "-" * 10
    n = 1
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    id = tool_call["id"]
                    tool_output = get_tool_output(messages, id)
                    if tool == "sql_db_query":
                        sql_query = tc_args["query"]
                        query_history += f"Step {n}. Executed SQL query: {sql_query}\nQuery Result: {tool_output}\n{breaker}\n"
                    else:
                        query_history += f"Step {n}. Called tool: {tool} - {tc_args}\nTool Output: {tool_output}\n{breaker}\n"
                    n += 1
    
            else:
                # did not make tool calls
                query_history += f"Assistant Output: {m.content}\n"
        
    return query_history

def assemble_history(messages):
    """
    messages: AI, TOOL, AI, TOOL, etc.
    """
    query_history = ""
    breaker = "-" * 10
    n = 1
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0 and m.content != "Repeated previous steps.":
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    id = tool_call["id"]
                    tool_output = get_tool_output(messages, id)
                    if tool == "sql_db_query":
                        sql_query = tc_args["query"]
                        query_history += f"Step {n}. Executed SQL query: {sql_query}\nQuery Result: {tool_output}\n{breaker}\n"
                    else:
                        query_history += f"Step {n}. Called tool: {tool} - {tc_args}\nTool Output: {tool_output}\n{breaker}\n"
                    n += 1
            elif m.content == "Repeated previous steps.":  # repeated steps
                query_history += f"Step {n}. Repeated tool calls from previous steps.\n{breaker}\n"
                n += 1
            else:
                # did not make tool calls
                query_history += f"Assistant Output: {m.content}\n"
        
    return query_history


def assemble_history_with_feedback(messages, chat_model):
    """
    messages: AI, TOOL, HUMAN, AI, TOOL, HUMAN, etc.
    """
    query_history = ""
    breaker = "-" * 10
    n = 1
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    id = tool_call["id"]
                    tool_output = get_tool_output(messages, id)
                    if tool == "sql_db_query":
                        # get feedback, the first human message after the tool call
                        feedback = ""
                        for i in range(messages.index(m), len(messages)):
                            if isinstance(messages[i], HumanMessage):
                                feedback = messages[i].content
                                break
                        sql_query = tc_args["query"]
                        query_history += f"Step {n}. Executed SQL query: {sql_query}\nQuery Result: {tool_output}\nReview of SQL query: {feedback}\n{breaker}\n"
                    else:
                        query_history += f"Step {n}. Called tool: {tool} - {tc_args}\nTool Output: {tool_output}\n{breaker}\n"
                    n += 1
            else:
                # did not make tool calls
                query_history += f"Assistant Output: {m.content}\n"

    # if len(query_history) > 1000:
    #     prompt = HISTORY_SUMMARY_PROMPT.format(steps=query_history)
    #     response = chat_model.invoke(prompt)
    #     # print("@@@ Summarized history:\n", response)
    #     query_history = response

    return query_history

if __name__ == "__main__":
    import os
    from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
    from langchain_community.utilities import SQLDatabase

    db_name = "california_schools"
    working_dir = os.getenv("WORKDIR")
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
    # test

#     #passed
    text = """\
To answer this question, we need to find the school with the lowest average score in reading in Southern California and then retrieve its telephone number.

First, let's identify the schools in Southern California. Southern California includes the following counties: Los Angeles, Orange, San Diego, San Bernardino, Riverside, Ventura, Santa Barbara, San Luis Obispo, Kern, and Imperial.

We can use the `schools` table to filter the schools by county. However, we need to join this table with the `satscores` table to get the average scores in reading.

Here's the query to get the schools in Southern California with their average scores in reading:

```sql
SELECT T1.cds, T1.AvgScrRead, T2.Phone 
FROM satscores AS T1 
```

This query joins the `satscores` table with the `schools` table on the `cds` column and filters the results to include only schools in Southern California.

However, we need to find the school with the lowest average score in reading. We can use the `ORDER BY` clause to sort the results by the average score in reading in ascending order and then use the `LIMIT` clause to get the first row, which corresponds to the school with the lowest average score.

Here's the updated query:

```sql
SELECT T1.cds, T1.AvgScrRead, T2.Phone 
FROM satscores AS T1 
INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode 
WHERE T2.County IN ('Los Angeles', 'Orange', 'San Diego', 'San Bernardino', 'Riverside', 'Ventura', 'Santa Barbara', 'San Luis Obispo', 'Kern', 'Imperial') 
ORDER BY T1.AvgScrRead ASC LIMIT 1;
```

This query will give us the school with the lowest average score in reading in Southern California and its telephone number.

```sql
TOOL CALL: {"tool": "search_web", "args": {"query": "most popular cities to visit among Oakland, Hayward, Newark, Fremont, Union City, San Leandro, Berkeley,Alameda, Pleasanton, Dublin"}}
```
Let's execute this query and get the result.
    """

    
    # parser = LlamaOutputParser()
    # output = parser.parse(text)
    # # print(output)
    # for x in output:
    #     if "tool" in x and x["tool"] == "sql_db_query":
    #         print("Query db....")
    #         print(db_query_tool.invoke({"query":x["args"]["query"]}))
    #     else:
    #         print(x)

    query_list = get_all_sql_queries(text)
    print(query_list)
    formatted_queries = format_sql_queries(query_list)
    print(formatted_queries)

    response = """
The most likely SQL query to provide the correct answer to the user question is:

3.

This query first joins the `satscores` table with the `schools` table to get the city and county information for each school. It then filters the results to
include only schools with an average math score over 560. Finally, it counts the number of schools in the Bay Area (defined as the counties 'Alameda', 'Contr
a Costa', 'Marin', 'Napa', 'San Francisco', 'San Mateo', 'Santa Clara', 'Solano', 'Sonoma').

Query 1 does not provide the location information, so it cannot answer the question. Query 2 provides the location information, but it does not count the num
ber of schools in the Bay Area.

"""

    for char in response:
        if char.isdigit():
            idx = int(char) - 1
            print(idx)
            break
     