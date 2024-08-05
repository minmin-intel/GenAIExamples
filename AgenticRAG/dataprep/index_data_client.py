import requests
import json
import argparse
import os

parser = argparse.ArgumentParser(description='Index data')
parser.add_argument('--host_ip', type=str, default='localhost', help='Host IP')
# parser.add_argument('--port', type=int, default=6007, help='Port')
parser.add_argument('--filedir', type=str, default=None, help='file directory')
parser.add_argument('--filename', type=str, default="crag_docs_music.jsonl", help='file name')
args = parser.parse_args()

host_ip = args.host_ip
proxies = {"http": ""}
url = "http://{host_ip}:6007/v1/dataprep".format(host_ip=host_ip)

file_list = [os.path.join(args.filedir, args.filename)]
files = [('files', (f, open(f, 'rb'))) for f in file_list]
resp = requests.request('POST', url=url, headers={}, files=files, proxies=proxies)
print(resp.text)
