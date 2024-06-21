#!/bin/bash
export host_ip=$(hostname -I | awk '{print $1}')
echo $host_ip

your_no_proxy=$no_proxy
your_no_proxy+=","
your_no_proxy+="${host_ip}"
echo $your_no_proxy

export no_proxy=${your_no_proxy}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
export EMBEDDING_MODEL_ID="BAAI/bge-base-en-v1.5"
export RERANK_MODEL_ID="BAAI/bge-reranker-base"
export LLM_MODEL_ID="meta-llama/Meta-Llama-3-8B-Instruct" #"Intel/neural-chat-7b-v3-3"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6006"
export TEI_RERANKING_ENDPOINT="http://${host_ip}:8808"
export TGI_LLM_ENDPOINT="http://${host_ip}:9009"
export REDIS_URL="redis://${host_ip}:6379"
export INDEX_NAME="rag-redis"
export HUGGINGFACEHUB_API_TOKEN=${your_hf_api_token}
# export HF_HOME=$HF_CACHE_DIR
export EMBEDDING_SERVICE_HOST_IP=${host_ip}
export RETRIEVER_SERVICE_HOST_IP=${host_ip}
export RERANK_SERVICE_HOST_IP=${host_ip}
export LLM_SERVICE_HOST_IP=${host_ip}

##### Mega service related configurations #############
export MEGA_SERVICE_HOST_IP=${host_ip}
export MEGA_SERVICE_NAME=retrievaltool #chatqna #ragtool # NEED TO CHANGE ACCORDING TO MEGA SERVICE!!!
export MEGA_SERVICE_PORT=8889 # NEED TO CHANGE ACCORDING TO MEGA SERVICE!!!
export BACKEND_SERVICE_ENDPOINT="http://${host_ip}:${MEGA_SERVICE_PORT}/v1/${MEGA_SERVICE_NAME}"
########################################################

export DATAPREP_SERVICE_ENDPOINT="http://${host_ip}:6007/v1/dataprep"

DOCKERCOMPOSEFILE=docker_compose_retrieval_tool.yaml #docker_compose_ragtool.yaml
docker compose -f xeon/$DOCKERCOMPOSEFILE up -d