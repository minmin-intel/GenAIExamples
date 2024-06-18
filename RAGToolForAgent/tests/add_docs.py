import requests
import json
host_ip = "localhost"
proxies = {"http": ""}
url = "http://{host_ip}:6007/v1/dataprep".format(host_ip=host_ip)
link1="https://www.intc.com/news-events/press-releases/detail/1692/intel-reports-first-quarter-2024-financial-results"
link2="https://www.intc.com/news-events/press-releases/detail/1672/intel-reports-fourth-quarter-and-full-year-2023-financial"
data = {"link_list":json.dumps([link1, link2])}
# payload = {"link_list": json.dumps(urls)}
# resp = requests.post(url=url, data=payload, proxies=proxies)
# print(json.dumps(data))
header = {"Content-Type": "multipart/form-data"}
response = requests.post(url, data=data)
print(response)
print(response.json())