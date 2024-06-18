import requests
import json
host_ip = "localhost"
proxies = {"http": ""}
url = "http://{host_ip}:8888/v1/chatqna".format(host_ip=host_ip)

query = "What is the revenue of Intel in 2023?"
data = {"messages":query}
header = {"Content-Type": "application/json"}
response = requests.post(url, json=data)
print(response)
# print(response.json())