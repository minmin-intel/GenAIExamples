import requests
import json
host_ip = "10.165.9.23"
proxies = {"http": ""}
megaservice = "retrievaltool"
port = "8889"
endpoint = "{port}/v1/{mega}".format(port = port, mega=megaservice)
url = "http://{host_ip}:{endpoint}".format(host_ip=host_ip, endpoint=endpoint)

query = "Nike reveneue in 2023"
data = {"text":query}
header = {"Content-Type": "application/json"}
response = requests.post(url, json=data, proxies=proxies, headers=header)
print(response)
print(response.json()["retrieved_docs"][0]["text"])
