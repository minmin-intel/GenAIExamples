# agent related environment variables
export TOOLSET_PATH=$WORKDIR/GenAIExamples/AgentQnA/tools/
echo "TOOLSET_PATH=${TOOLSET_PATH}"
export recursion_limit_worker=12
export recursion_limit_supervisor=10
# export WORKER_AGENT_URL="http://${ip_address}:9095/v1/chat/completions"
# export RETRIEVAL_TOOL_URL="http://${ip_address}:8889/v1/retrievaltool"
# export CRAG_SERVER=http://${ip_address}:8080

export WORKER_AGENT_URL="http://localhost:9095/v1/chat/completions"
export RETRIEVAL_TOOL_URL="http://localhost:8889/v1/retrievaltool"
export CRAG_SERVER="http://localhost:8080"

python test.py
