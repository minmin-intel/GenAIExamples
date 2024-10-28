port=8085
vllm_volume=$HF_CACHE_DIR
HF_TOKEN=$HUGGINGFACEHUB_API_TOKEN
model="meta-llama/Meta-Llama-3.1-70B-Instruct"
docker run -d --runtime=habana --rm --name "comps-vllm-gaudi-service" -p $port:80 -v $vllm_volume:/data -e HF_TOKEN=$HF_TOKEN -e HF_HOME=/data -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e VLLM_SKIP_WARMUP=true -e VLLM_RAY_DISABLE_LOG_TO_DRIVER=1 --cap-add=sys_nice --ipc=host opea/vllm:hpu --model ${model} --host 0.0.0.0 --port 80 --block-size 128 --max-num-seqs  8192 --max-seq_len-to-capture 16384 --tensor-parallel-size 4