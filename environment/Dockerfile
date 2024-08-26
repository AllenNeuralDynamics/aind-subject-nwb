# hash:sha256:679ba4116b5b926467b5b0752f1ee9df0177a9ce7c82691e3b6096adfb7fdc11
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/jupyterlab:3.6.1-miniconda4.12.0-python3.9-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install -U --no-cache-dir \
    aind-data-access-api==0.6.1 \
    boto3==1.28.72 \
    hdmf-zarr==0.8.0 \
    pynwb==2.8.1
