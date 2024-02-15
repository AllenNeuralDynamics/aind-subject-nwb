# hash:sha256:e04473a99a2b34860b27e200192b0f6371b92904702ebd8b313ff2733e53fb8a
FROM registry.codeocean.allenneuraldynamics.org/codeocean/jupyterlab:3.6.1-miniconda4.12.0-python3.9-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install -U --no-cache-dir \
    aind-data-access-api==0.6.1 \
    boto3==1.28.72 \
    hdmf-zarr==0.5.0 \
    pynwb==2.5.0
