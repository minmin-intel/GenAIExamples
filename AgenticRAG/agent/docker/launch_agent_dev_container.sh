host_ip=$(hostname -I | awk '{print $1}')
export LLM_MODEL_ID=meta-llama/Meta-Llama-3-8B-Instruct #"Intel/neural-chat-7b-v3-3" #meta-llama/Meta-Llama-3-70B-Instruct #
export TGI_LLM_ENDPOINT="http://${host_ip}:9009"
export CRAG_SERVER=http://${host_ip}:8080
export RETRIEVAL_TOOL_URL=http://${host_ip}:8889/v1/retrievaltool
export OPENAI_API_KEY=${OPENAI_API_KEY}

docker compose -f docker_compose_agent.yaml up -d