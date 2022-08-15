FROM python:3.7-buster

RUN echo "sw-r2d2-bot:$1$fYEQITJi$PvkO0KuNGp68VQZ7jOrv60:7331:30:MLNXshared DevOps, Vladi Ifat:/labhome/sw-r2d2-bot:/bin/bash" >> /etc/passwd

RUN apt-get update && \
    apt-get -y install sudo && \
    apt-get install -y virtualenv

RUN mkdir ./nvos
COPY ./unittests/requirements.txt ./nvos/requirements.txt
COPY ./unittests/run_unittests.py ./nvos/run_unittests.py
COPY ./nvos ./nvos

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./nvos/requirements.txt && \
    pip install --ignore-installed ruamel.yaml && \
    pip install --no-dependencies jsonschema==3.2.0

LABEL version="1.0"
LABEL description="Docker image for NVOS Unittests"

CMD [ "python3", "./nvos/run_unittests.py"]
