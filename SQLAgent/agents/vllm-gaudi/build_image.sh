WORKPATH=$WORKDIR
function build_vllm_docker_images() {
    echo "Building the vllm docker images"
    cd $WORKPATH
    echo $WORKPATH
    if [ ! -d "./vllm" ]; then
        git clone https://github.com/HabanaAI/vllm-fork.git
    fi
    cd ./vllm-fork
    docker build -f Dockerfile.hpu -t opea/vllm:hpu --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
    if [ $? -ne 0 ]; then
        echo "opea/vllm:hpu failed"
        exit 1
    else
        echo "opea/vllm:hpu successful"
    fi
}

build_vllm_docker_images