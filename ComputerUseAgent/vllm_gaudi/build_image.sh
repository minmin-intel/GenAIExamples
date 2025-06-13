image=vllm-gaudi:qwen25-vl
docker build --no-cache -f Dockerfile_qwen25vl -t $image . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    