#!/bin/bash

docker run -it --name annotation \
--runtime=habana -e HABANA_VISIBLE_DEVICES=all \
-e OMPI_MCA_btl_vader_single_copy_mechanism=none \
-v $WORKDIR:/home/user/workspace \
--cap-add=sys_nice \
--net=host \
--env http_proxy=${http_proxy} \
--env https_proxy=${https_proxy} \
--env HF_HOME=$HF_HOME \
--env HUGGING_FACE_HUB_TOKEN=$HUGGING_FACE_HUB_TOKEN \
--ipc=host annotation-gaudi:latest