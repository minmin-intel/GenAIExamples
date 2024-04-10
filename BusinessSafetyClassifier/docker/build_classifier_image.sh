#!/bin/bash
dockerfile=Dockerfile.classifier

docker build \
    -f ${dockerfile} . \
    -t classifier:latest \
    --network=host \
    --build-arg http_proxy=${http_proxy} \
    --build-arg https_proxy=${https_proxy} \
    --build-arg no_proxy=${no_proxy} \