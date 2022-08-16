FROM ubuntu:18.04

RUN echo "sw-r2d2-bot:$1$fYEQITJi$PvkO0KuNGp68VQZ7jOrv60:7331:30:MLNXshared DevOps, Vladi Ifat:/labhome/sw-r2d2-bot:/bin/bash" >> /etc/passwd

RUN apt-get update && \
    apt-get -y install sudo && \
    apt-get install -y python3-pip git

RUN mkdir ./nvos
COPY ./unittests/requirements.txt ./nvos/requirements.txt
COPY ./unittests/run_unittests.py ./nvos/run_unittests.py
COPY ./nvos ./nvos

RUN pip3 install --no-cache-dir --upgrade pip
RUN apt-get install -y python3-virtualenv python3.7-venv
RUN pip3 install --ignore-installed ruamel.yaml
RUN pip3 install --no-dependencies jsonschema==3.2.0

LABEL version="1.0"
LABEL description="Docker image for NVOS Unittests"

CMD [ "python3", "./nvos/run_unittests.py"]
