import requests
import json
import argparse
import os
import pandas as pd


def generate_answer(url, prompt):
    proxies = {"http": ""}
    payload = {
        "query":prompt,
        # "max_new_tokens":args.max_new_tokens,
        # "top_k":10,
        # "top_p":0.95,
        # # "typical_p":0.95,
        # "temperature":0.01,
        # "repetition_penalty":1.03,
        # "streaming":False
        } 
    response = requests.post(url, json=payload, proxies=proxies) #, headers=header)
    print(response)
    return response.json()["text"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host_ip", type=str, default="localhost", help="host ip of the retrieval tool")
    parser.add_argument("--query_file", type=str, default=None, help="query jsonl file")
    parser.add_argument("--output_file", type=str, default="output.jsonl", help="output jsonl file")
    parser.add_argument("--max_new_tokens", type=int, default=128, help="max new tokens for the generator")
    args = parser.parse_args()
    
    host_ip = args.host_ip
    port = "9090"
    endpoint = "{port}/v1/chat/completions".format(port = port)
    url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=endpoint)

    output_list = []

    if args.query_file.endswith('.jsonl'):
        df = pd.read_json(args.query_file, lines=True, convert_dates=False)
    elif args.query_file.endswith('.csv'):
        df = pd.read_csv(args.query_file)
    
    n = 0
    for _, row in df.iterrows():
        q = row['query']
        t = row['query_time']
        prompt = "Question: {} \nThe question was asked at: {}".format(q, t)
        answer = generate_answer(url, prompt)
        print(answer)
        print('-------------------')