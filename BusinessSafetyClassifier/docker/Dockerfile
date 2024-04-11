FROM vault.habana.ai/gaudi-docker/1.15.1/ubuntu22.04/habanalabs/pytorch-installer-2.2.0:latest
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /home/user
COPY requirements.txt /home/user/
RUN pip install -r requirements.txt
# RUN pip install --upgrade-strategy eager optimum[habana]
RUN pip install optimum-habana