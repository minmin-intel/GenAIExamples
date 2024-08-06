import requests
import json
import argparse
import pandas as pd

def query_retrieval_tool(url, query):
    data = {"text":query}
    header = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, proxies=proxies) #, headers=header)
    # print(response)
    print(response.json()["text"])

def get_test_dataset(args):
    if args.query_file.endswith('.jsonl'):
        df = pd.read_json(args.query_file, lines=True, convert_dates=False)
    elif args.query_file.endswith('.csv'):
        df = pd.read_csv(args.query_file)
    else:
        raise ValueError("Invalid file format")
    return df
            


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host_ip", type=str, default="localhost", help="host ip of the retrieval tool")
    parser.add_argument("--query_file", type=str, default=None, help="query jsonl file")
    args = parser.parse_args()
    
    host_ip = args.host_ip
    proxies = {"http": ""}
    megaservice = "retrievaltool"
    port = "8889"
    endpoint = "{port}/v1/{mega}".format(port = port, mega=megaservice)
    url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=endpoint)

    df = get_test_dataset(args)

    for n, row in df.iterrows():
        q = row['query']
        print('Query: {}'.format(q))
        query_retrieval_tool(url, q)
        if n >2:
            break

