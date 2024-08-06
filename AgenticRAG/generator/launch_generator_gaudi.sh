host_ip=$(hostname -I | awk '{print $1}')
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-70B-Instruct" #"meta-llama/Meta-Llama-3-8B-Instruct" #"Intel/neural-chat-7b-v3-3" #"meta-llama/Meta-Llama-3-70B-Instruct" #
export TGI_LLM_ENDPOINT="http://${host_ip}:8008"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_SERVICE_HOST_IP=${host_ip}

docker compose -f docker_compose_generator_gaudi.yaml up -d