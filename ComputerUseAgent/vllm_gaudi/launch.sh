model="ByteDance-Seed/UI-TARS-1.5-7B" # fine-tuned from qwen2.5vl
MAX_INPUT=65536
vllm_port=8086
vllm_volume=$HF_CACHE_DIR
echo "token is ${HF_TOKEN}"
LOG_PATH=$WORKDIR
image=vllm-gaudi:qwen25-vl

echo "start vllm gaudi service"
echo "**************model is $model**************"
docker run -d --runtime=habana --rm --name "vllm-gaudi-server" -e HABANA_VISIBLE_DEVICES=0 -p $vllm_port:80 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN -e HF_HOME=/data -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e PT_HPUGRAPH_DISABLE_TENSOR_CACHE=false -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy -e VLLM_SKIP_WARMUP=true --cap-add=sys_nice --ipc=host $image --model ${model} --host 0.0.0.0 --port 80 --max-seq-len-to-capture $MAX_INPUT --limit-mm-per-prompt image=8 #--tensor-parallel-size 4