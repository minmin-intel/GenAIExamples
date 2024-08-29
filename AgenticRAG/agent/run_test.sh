export TGI_LLM_ENDPOINT=http://${host_ip}:8085
export RETRIEVAL_TOOL_URL=http://${host_ip}:8889/v1/retrievaltool
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

python3 test.py