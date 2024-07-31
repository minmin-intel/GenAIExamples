import requests
import json
import argparse
import os
import pandas as pd


proxies = {"http": ""}

def get_query(args):
    query = []
    query_time = []
    n = 0
    with open(args.query_file, "r") as f:
        for line in f:
            data = json.loads(line)
            query.append(data["query"])
            query_time.append(data["query_time"])
            # n += 1
            # if n >= 2:
            #     break
    return query, query_time

def query_retrieval_tool(url, query):
    data = {"text":query}
    header = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, proxies=proxies) #, headers=header)
    return response.json()["text"]

## V0 baseline ###
# PROMPT = """\
# ### You are a helpful, respectful and honest assistant to help the user with questions. \
# Please refer to the search results obtained from the local knowledge base. \
# But be careful to not incorporate the information that you think is not relevant to the question. \
# If you don't know the answer to a question, please don't share false information. \
# ### Search results: {context} \n
# ### Question: {question} \n
# ### Answer:
# """
#################

PROMPT = """\
### You are a helpful, respectful and honest assistant.
You are given a Question and the time when it was asked in the Pacific Time Zone (PT), referred to as "Query
Time". The query time is formatted as "mm/dd/yyyy, hh:mm:ss PT".
Please follow these guidelines when formulating your answer:
1. If the question contains a false premise or assumption, answer “invalid question”.
2. If you are uncertain or do not know the answer, respond with “I don’t know”.
3. Refer to the search results to form your answer.
5. Give concise, factual and relevant answers.

### Search results: {context} \n
### Question: {question} \n
### Query Time: {time} \n
### Answer:
"""

def generate_answer(args, url, query, context, time):
    prompt = PROMPT.format(context=context, question=query, time=time)
    payload = {
        "query":prompt,
        "max_new_tokens":args.max_new_tokens,
        "top_k":10,
        "top_p":0.95,
        # "typical_p":0.95,
        "temperature":0.01,
        "repetition_penalty":1.03,
        "streaming":False
        } 
    response = requests.post(url, json=payload, proxies=proxies) #, headers=header)
    return response.json()["text"]

def generate_answer_openai(args, query, context, time):
    from langchain_openai import ChatOpenAI
    prompt = PROMPT.format(context=context, question=query, time=time)
    llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18", max_tokens=args.max_new_tokens, temperature=0)
    messages = [
        ("human", prompt)
    ]
    ai_msg = llm.invoke(messages)
    # print(ai_msg.content)
    return ai_msg.content



def save_results(args, output_list):
    if not os.path.exists(os.path.dirname(args.output_file)):
        os.makedirs(os.path.dirname(args.output_file))
        
    with open(args.output_file, "a") as f:
        for output in output_list:
            f.write(json.dumps(output))
            f.write("\n")

def save_as_csv(args):
    df = pd.read_json(args.output_file, lines=True, convert_dates=False)
    df.to_csv(args.output_file.replace(".jsonl", ".csv"), index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host_ip", type=str, default="localhost", help="host ip of the retrieval tool")
    parser.add_argument("--query_file", type=str, default=None, help="query jsonl file")
    parser.add_argument("--output_file", type=str, default="output.jsonl", help="output jsonl file")
    parser.add_argument("--max_new_tokens", type=int, default=128, help="max new tokens for the generator")
    parser.add_argument("--use_openai", action="store_true", help="use openai API")
    args = parser.parse_args()
    
    host_ip = args.host_ip
    megaservice = "retrievaltool"
    port = "8889"
    retrieval_endpoint = "{port}/v1/{mega}".format(port = port, mega=megaservice)
    retrieval_url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=retrieval_endpoint)

    port = "9000"
    generator_endpoint = "{port}/v1/chat/completions".format(port = port)
    generator_url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=generator_endpoint)

    # query_list, query_time = get_query(args)
    # context_list = []
    # answer_list = []
    output_list = []

    if args.query_file.endswith('.jsonl'):
        df = pd.read_json(args.query_file, lines=True, convert_dates=False)
    elif args.query_file.endswith('.csv'):
        df = pd.read_csv(args.query_file)
    
    n = 0
    for _, row in df.iterrows():
        q = row['query']
        t = row['query_time']
        print('Query: {}'.format(q))
        print('Query Time: {}'.format(t))
        context = query_retrieval_tool(retrieval_url, q)
        print('Context:\n{}'.format(context))
        if args.use_openai:
            answer = generate_answer_openai(args, q, context, t)
        else:
            answer = generate_answer(args, generator_url, q, context, t)
        print('Answer:\n{}'.format(answer))
        print('-'*50)
        
        # answer_list.append(answer)
        # context_list.append(context)  
        output_list.append(
            {"query":q, 
             "query_time":t, 
             "context":context, 
             "answer":answer,
             "question_type":row['question_type'],
             "static_or_dynamic":row['static_or_dynamic'],
             "ref_answer":row['answer'],})      
        n+=1
        # if n>=2:
        #     break
        if n > 0 and n%10 == 0:
            save_results(args, output_list)
            output_list = []
    
    save_results(args, output_list)
    save_as_csv(args)


