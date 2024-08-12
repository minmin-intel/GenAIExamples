export ip_address=$(hostname -I | awk '{print $1}')
export strategy=docgrader
export recursion_limit=10
export model="mistralai/Mistral-7B-Instruct-v0.3" #"meta-llama/Meta-Llama-3-8B-Instruct"
export temperature=0
export max_new_tokens=512
export streaming=true
export TGI_LLM_ENDPOINT="http://${ip_address}:9009"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}

docker compose -f docker_compose_agent_tgi.yaml up -d

