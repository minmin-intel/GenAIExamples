import requests
import json
import argparse
import os


proxies = {"http": ""}

def get_query(args):
    query = []
    n = 0
    with open(args.query_file, "r") as f:
        for line in f:
            data = json.loads(line)
            query.append(data["query"])
            # n += 1
            # if n >= 2:
            #     break
    return query

def query_retrieval_tool(url, query):
    data = {"text":query}
    header = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, proxies=proxies) #, headers=header)
    return response.json()["text"]


PROMPT = """\
### You are a helpful, respectful and honest assistant to help the user with questions. \
Please refer to the search results obtained from the local knowledge base. \
But be careful to not incorporate the information that you think is not relevant to the question. \
If you don't know the answer to a question, please don't share false information. \
### Search results: {context} \n
### Question: {question} \n
### Answer:
"""

def generate_answer(url, query, context):
    prompt = PROMPT.format(context=context, question=query)
    payload = {
        "query":prompt,
        "max_new_tokens":128,
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
    args = parser.parse_args()
    
    host_ip = args.host_ip
    megaservice = "retrievaltool"
    port = "8889"
    retrieval_endpoint = "{port}/v1/{mega}".format(port = port, mega=megaservice)
    retrieval_url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=retrieval_endpoint)

    port = "9000"
    generator_endpoint = "{port}/v1/chat/completions".format(port = port)
    generator_url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=generator_endpoint)

    query_list = get_query(args)
    output_list = []

    n = 0
    for q in query_list:
        print('Query: {}'.format(q))
        context = query_retrieval_tool(retrieval_url, q)
        print('Context:\n{}'.format(context))
        answer = generate_answer(generator_url, q, context)
        print('Answer:\n{}'.format(answer))
        print('-'*50)
        output_list.append({"query":q, "context":context, "answer":answer})
        n+=1
        if n > 0 and n%10 == 0:
            save_results(args, output_list)
            output_list = []
    
    save_results(args, output_list)
        


