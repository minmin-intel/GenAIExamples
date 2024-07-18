import requests
import json
import argparse

def query_retrieval_tool(url, query):
    data = {"text":query}
    header = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, proxies=proxies) #, headers=header)
    print(response)
    print(response.json()["retrieved_docs"][0]["text"])

def get_query(args):
    query = []
    n = 0
    with open(args.query_file, "r") as f:
        for line in f:
            data = json.loads(line)
            query.append(data["query"])
            n += 1
            if n > 3:
                break
    return query
            


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

    query_list = get_query(args)

    for q in query_list:
        print('Query: {}'.format(q))
        query_retrieval_tool(url, q)

