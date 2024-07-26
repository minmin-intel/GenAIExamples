# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM python:3.11-slim

ENV LANG C.UTF-8

RUN apt-get update -y && apt-get install -y --no-install-recommends --fix-missing \
    build-essential \
    libgl1-mesa-glx \
    libjemalloc-dev

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/

USER user

# COPY comps /home/user/comps
COPY agent /home/user/agent

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    if [ ${ARCH} = "cpu" ]; then pip install torch --index-url https://download.pytorch.org/whl/cpu; fi && \
    pip install --no-cache-dir -r /home/user/agent/docker/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/home/user

# USER root

# RUN mkdir -p /home/user/comps/agent/langchain/status && chown -R user /home/user/comps/agent/langchain/status

# USER user
RUN mkdir -p /home/user/datasets/

WORKDIR /home/user/agent/

ENTRYPOINT ["python", "test.py"]