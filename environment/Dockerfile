# hash:sha256:36e5b83aa55132da4b5b7362b8504118434221ba49398957015d4d6f617f14ff
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/jupyterlab:3.6.1-miniconda4.12.0-python3.9-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install -U --no-cache-dir \
    aind-data-access-api==0.6.1 \
    aind-log-utils==0.2.1 \
    boto3==1.28.72 \
    hdmf-zarr==0.8.0 \
    pynwb==2.8.1
