import requests
import json
import argparse
import os
import pandas as pd


def generate_answer(url, prompt):
    proxies = {"http": ""}
    payload = {
        "query":prompt,
        } 
    response = requests.post(url, json=payload, proxies=proxies) #, headers=header)
    # print(response)
    return response.json()["text"]

def save_results(output_file, output_list):       
    with open(output_file, "w") as f:
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
    port = "9090"
    endpoint = "{port}/v1/chat/completions".format(port = port)
    url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=endpoint)


    if args.query_file.endswith('.jsonl'):
        df = pd.read_json(args.query_file, lines=True, convert_dates=False)
    elif args.query_file.endswith('.csv'):
        df = pd.read_csv(args.query_file)
    
    query= [
            "weather in san francisco",
            # "how many songs has the band the beatles released that have been recorded at abbey road studios?",
            # "what's the most recent album from the founder of ysl records?",
            # "when did dolly parton's song, blown away, come out?"
            # "what song topped the billboard chart on 2004-02-04?",
            # "what grammy award did edgar barrera win this year?",
            # "who has had more number one hits on the us billboard hot 100 chart, michael jackson or elvis presley?",
        ]
    query_time=[
        "08/11/2024, 23:37:29 PT", 
        # "03/21/2024, 23:37:29 PT",
        # "03/21/2024, 23:37:29 PT",
        # "03/21/2024, 23:37:29 PT",
        ]
    df = pd.DataFrame({"query": query, "query_time": query_time})
    
    output_list = []
    n = 0
    for _, row in df.iterrows():
        q = row['query']
        t = row['query_time']
        prompt = "Question: {}\nThe question was asked at: {}".format(q, t)
        print('******Prompt:\n',prompt)
        print("******Agent is working on the query")
        # generate_answer(url, prompt)
        # print('='*50)
        answer = generate_answer(url, prompt)
        print('******Answer from agent:\n',answer)
        print('='*50)
        output_list.append(
                {
                    "query": q,
                    "query_time": t,
                    "ref_answer": row["answer"],
                    "answer": answer,
                    # "context": context,
                    # "num_llm_calls": n+NUM_LLM_CALLS_BY_RETRIEVAL_TOOL,
                    # "total_tokens": ntok+NUM_TOKENS_BY_RETRIEVAL_TOOL,
                    "question_type": row["question_type"],
                    "static_or_dynamic": row["static_or_dynamic"],
                }
            )
        save_results(args.output_file, output_list)
        n += 1
        if n > 1:
            break