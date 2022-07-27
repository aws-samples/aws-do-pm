# FROM rapidsai/rapidsai:21.06-cuda11.0-runtime-ubuntu18.04-py3.7
FROM rapidsai/rapidsai:21.06-cuda11.0-base-ubuntu18.04


RUN apt-get update -y && \
    apt-get install gcc g++ gfortran nano -y

RUN apt-get install curl unzip -y && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

COPY requirements.txt .
RUN /bin/bash -c ". activate rapids" && \
    /opt/conda/envs/rapids/bin/pip install -r requirements.txt

COPY src /wd

WORKDIR /wd
