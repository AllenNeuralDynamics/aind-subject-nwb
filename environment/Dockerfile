# hash:sha256:489aa6cfe0be1cca13dc47201e9f68504e4813b1a92313f5fdf1bd7697777fa3
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/jupyterlab:3.6.1-miniconda4.12.0-python3.9-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive
ARG AWS_ACCESS_KEY_ID
ARG AWS_DEFAULT_REGION
ARG AWS_SECRET_ACCESS_KEY

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install -U --no-cache-dir \
    aind-data-access-api==0.6.1 \
    aind-log-utils==0.2.3 \
    boto3==1.28.72 \
    hdmf-zarr==0.11.0 \
    pynwb==2.8.3
