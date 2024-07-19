host_ip=$(hostname -I | awk '{print $1}')
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3" #"meta-llama/Meta-Llama-3-8B-Instruct" #
export TGI_LLM_ENDPOINT="http://${host_ip}:9009"
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_SERVICE_HOST_IP=${host_ip}

docker compose -f docker_compose_generator.yaml up -d

