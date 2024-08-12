export ip_address=$(hostname -I | awk '{print $1}')
export strategy=docgrader
export recursion_limit=10
export model="gpt-4o-mini-2024-07-18"
export temperature=0
export max_new_tokens=512
export streaming=true
export OPENAI_API_KEY=${OPENAI_API_KEY}

docker compose -f docker_compose_agent_openai.yaml up -d

