import uuid
import json
from langchain_core.messages.tool import ToolCall
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage


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
    json_lines = text.split("\n")
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

class LlamaOutputParser(BaseOutputParser):
    """
    Assumptions:
    1. the final sql query in raw llm output is the query that agent wants to execute.
    2. If FINAL ANSWER is in text, it should be considered agent's answer even though there might stil be tool calls in the text.
    3. If other tools like search_web, etc. are called together with sql query tool, the other tools should take priority over sql_db_query, to first gather related info first.
    """
    def parse(self, text: str):
        print("@@@ Raw output from llm:\n", text)

        if "FINAL ANSWER:" in text:
            return [{"answer": text.split("FINAL ANSWER:")[-1]}]
        else:
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


def assemble_history(messages):
    """
    messages: AI, TOOL, AI, TOOL, etc.
    """
    query_history = ""
    breaker = "-" * 10
    for m in messages[1:]:  # exclude the first message
        if isinstance(m, AIMessage):
            # if there is tool call
            if hasattr(m, "tool_calls") and len(m.tool_calls) > 0:
                for tool_call in m.tool_calls:
                    tool = tool_call["name"]
                    tc_args = tool_call["args"]
                    id = tool_call["id"]
                    tool_output = get_tool_output(messages, id)
                    query_history += f"Tool Call: {tool} - {tc_args}\nTool Output: {tool_output}\n{breaker}\n"
            else:
                # did not make tool calls
                query_history += f"Assistant Output: {m.content}\n"

    return query_history


def assemble_history_with_feedback(messages):
    """
    messages: AI, TOOL, HUMAN, AI, TOOL, HUMAN, etc.
    """
    query_history = ""
    breaker = "-" * 10
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

                        query_history += f"Executed SQL query: {tc_args}\nResult: {tool_output}\nReview of SQL query: {feedback}\n{breaker}\n"
                    else:
                        query_history += f"Called tool: {tool} - {tc_args}\nTool Output: {tool_output}\n{breaker}\n"
            else:
                # did not make tool calls
                query_history += f"Assistant Output: {m.content}\n"

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

    # passed
    text = """\
    To answer this question, we need to find the schools in the Bay Area with an average score in Math over 560 in the SAT test. 

First, we need to identify the schools in the Bay Area. The Bay Area includes several counties, including Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, and Sonoma. We can use the `schools` table to find the schools in these counties.
First, we need to find the counties with a population over 2 million. However, the provided database schema does not contain information about the population of counties. Therefore, we will use the web search tool to find the counties in California with a population over 2 million.

TOOL CALL: {"tool": "search_web", "args": {"query": "counties in California with population over 2 million"}}

After finding the counties with a population over 2 million, we will use the database to find the number of test takers at schools in those counties. We can do this by joining the 'satscores' table with the 'schools' table on the 'CDSCode' column, and then filtering the results to only include schools in the counties we found earlier.
Next, we need to find the schools with an average score in Math over 560 in the SAT test. We can use the `satscores` table to find this information.

Here's a SQL query that combines the information from both tables:

```sql
SELECT COUNT(T1.CDSCode) 
FROM schools AS T1 
INNER JOIN satscores AS T2 
ON T1.CDSCode = T2.cds 
WHERE T1.County IN ('Alameda', 'Contra Costa', 'Marin', 'Napa', 'San Francisco', 'San Mateo', 'Santa Clara', 'Solano', 'Sonoma') 
AND T2.AvgScrMath > 560
```

This query joins the `schools` table with the `satscores` table on the `CDSCode` column, which is common to both tables. It then selects the schools in the Bay Area counties and with an average score in Math over 560.

Let's execute this query to get the answer.
TOOL CALL: {"tool": "search_web", "args": {"query": "Search again counties in California with population over 2 million"}}
TOOL CALL: {"tool": "sql_db_query", "args": {"query": "SELECT COUNT(T1.CDSCode) FROM schools AS T1 INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds WHERE T1.County IN (\'Alameda\', \'Contra Costa\', \'Marin\', \'Napa\', \'San Francisco\', \'San Mateo\', \'Santa Clara\', \'Solano\', \'Sonoma\') AND T2.AvgScrMath > 560"}}
    """


#     #passed
    text = """\
To answer this question, we need to find the school with the lowest average score in reading in Southern California and then retrieve its telephone number.

First, let's identify the schools in Southern California. Southern California includes the following counties: Los Angeles, Orange, San Diego, San Bernardino, Riverside, Ventura, Santa Barbara, San Luis Obispo, Kern, and Imperial.

We can use the `schools` table to filter the schools by county. However, we need to join this table with the `satscores` table to get the average scores in reading.

Here's the query to get the schools in Southern California with their average scores in reading:

```sql
SELECT T1.cds, T1.AvgScrRead, T2.Phone 
FROM satscores AS T1 
INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode 
WHERE T2.County IN ('Los Angeles', 'Orange', 'San Diego', 'San Bernardino', 'Riverside', 'Ventura', 'Santa Barbara', 'San Luis Obispo', 'Kern', 'Imperial');
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

TOOL CALL: sql_db_query - {'query': "SELECT T1.cds, T1.AvgScrRead, T2.Phone FROM satscores AS T1 INNER JOIN schools AS T2 ON T1.cds = T2.CDSCode WHERE T2.County IN ('Los Angeles', 'Orange', 'San Diego', 'San Bernardino', 'Riverside', 'Ventura', 'Santa Barbara', 'San Luis Obispo', 'Kern', 'Imperial') ORDER BY T1.AvgScrRead ASC LIMIT 1;"}

Let's execute this query and get the result.
    """

    # passed
    text = """\
Let's assume the query returns the following schools:

| CDSCode | County | District | School | AvgScrMath |
| --- | --- | --- | --- | --- |
| 12345 | Riverside | Riverside Unified | Riverside High School | 420 |
| 67890 | Riverside | Riverside Unified | John W. North High School | 450 |

Now, let's analyze the qualities of these schools based on the information provided in the `schools` table.

```sql
SELECT * 
FROM schools 
WHERE CDSCode IN ('12345', '67890');
```

This query will return all the columns for the schools with `CDSCode` 12345 and 67890.

Based on the information provided in the `schools` table, we can analyze the qualities of these schools, such as their status type, street address, city, zip code, phone number, website, and more.

FINAL ANSWER: The schools in Riverside where the average math score for SAT is greater than 400 are Riverside High School and John W. North High School. Their qualities can be analyzed based on the information provided in the `schools` table.
    """
    parser = LlamaOutputParser()
    output = parser.parse(text)
    # print(output)
    for x in output:
        if "tool" in x and x["tool"] == "sql_db_query":
            print("Query db....")
            print(db_query_tool.invoke({"query":x["args"]["query"]}))
        else:
            print(x)
     