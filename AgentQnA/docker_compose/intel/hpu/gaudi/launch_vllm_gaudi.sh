# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

model="meta-llama/Llama-3.3-70B-Instruct" #"meta-llama/Meta-Llama-3.1-70B-Instruct" #"deepseek-ai/DeepSeek-R1-Distill-Llama-70B" #
vllm_port=8086
vllm_volume=${HF_CACHE_DIR}
LOG_PATH=${WORKDIR}
vllm_image="opea/vllm-gaudi:ci"
max_length=131072 #16384

echo "start vllm gaudi service"
echo "**************model is $model**************"
docker run -d --runtime=habana --rm --name "vllm-gaudi-server" -e HABANA_VISIBLE_DEVICES=0,1,2,3 -p $vllm_port:80 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host  $vllm_image --model ${model} --host 0.0.0.0 --port 80 --block-size 128 --max-seq-len-to-capture $max_length --tensor-parallel-size 4
# sleep 5s