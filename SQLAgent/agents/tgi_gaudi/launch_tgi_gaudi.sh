# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# echo "WORKDIR=${WORKDIR}"
# export ip_address=$(hostname -I | awk '{print $1}')

# LLM related environment variables
export HF_CACHE_DIR=${HF_CACHE_DIR}
ls $HF_CACHE_DIR
export HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN}
export LLM_MODEL_ID="meta-llama/Meta-Llama-3.1-70B-Instruct"
# export NUM_SHARDS=4
# export LLM_ENDPOINT_URL="http://${ip_address}:8085"
# export temperature=0.01
# export max_new_tokens=128

docker compose -f compose.yaml up -d
