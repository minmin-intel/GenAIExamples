#!/bin/bash

volume=$WORKDIR

docker run -it -v $volume:/home/user/workspace --env http_proxy=${http_proxy} --env https_proxy=${https_proxy} classifier:latest