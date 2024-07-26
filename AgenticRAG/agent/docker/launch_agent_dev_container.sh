host_ip=$(hostname -I | awk '{print $1}')
export LLM_MODEL_ID="Intel/neural-chat-7b-v3-3"
export TGI_LLM_ENDPOINT="http://${host_ip}:9009"
export CRAG_SERVER=http://${host_ip}:8080
export RETRIEVAL_TOOL_URL=http://${host_ip}:8889/v1/retrievaltool

docker compose -f docker_compose_agent.yaml up -d