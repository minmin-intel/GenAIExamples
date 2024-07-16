# export no_proxy=${your_no_proxy}
# export http_proxy=${your_http_proxy}
# export https_proxy=${your_http_proxy}
host_ip=$(hostname -I | awk '{print $1}')
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
# export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
# export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
# export HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN

docker compose -f docker_compose_dataprep.yaml up -d