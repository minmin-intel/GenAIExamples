import requests
import json
host_ip = "localhost"
proxies = {"http": ""}
url = "http://{host_ip}:6007/v1/dataprep".format(host_ip=host_ip)

file_list = ["/localdisk/minminho/datasets/crag_docs/crag_docs_music.jsonl"]
files = [('files', (f, open(f, 'rb'))) for f in file_list]
resp = requests.request('POST', url=url, headers={}, files=files, proxies=proxies)
print(resp.text)
