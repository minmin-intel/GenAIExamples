import requests
import json
import argparse
import os


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

def save_results(args, output_list):
    if not os.path.exists(os.path.dirname(args.output_file)):
        os.makedirs(os.path.dirname(args.output_file))
        
    with open(args.output_file, "a") as f:
        for output in output_list:
            f.write(json.dumps(output))
            f.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host_ip", type=str, default="localhost", help="host ip of the retrieval tool")
    parser.add_argument("--query_file", type=str, default=None, help="query jsonl file")
    parser.add_argument("--output_file", type=str, default="output.jsonl", help="output jsonl file")
    parser.add_argument("--max_new_tokens", type=int, default=128, help="max new tokens for the generator")
    args = parser.parse_args()
    
    host_ip = args.host_ip
    megaservice = "retrievaltool"
    port = "8889"
    retrieval_endpoint = "{port}/v1/{mega}".format(port = port, mega=megaservice)
    retrieval_url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=retrieval_endpoint)

    port = "9000"
    generator_endpoint = "{port}/v1/chat/completions".format(port = port)
    generator_url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=generator_endpoint)

    query_list, query_time = get_query(args)
    output_list = []

    n = 0
    for q, t in zip(query_list, query_time):
        print('Query: {}'.format(q))
        print('Query Time: {}'.format(t))
        context = query_retrieval_tool(retrieval_url, q)
        print('Context:\n{}'.format(context))
        answer = generate_answer(args, generator_url, q, context, t)
        print('Answer:\n{}'.format(answer))
        print('-'*50)
        output_list.append({"query":q, "context":context, "answer":answer})
        n+=1
        if n > 0 and n%10 == 0:
            save_results(args, output_list)
            output_list = []
    
    save_results(args, output_list)
        


