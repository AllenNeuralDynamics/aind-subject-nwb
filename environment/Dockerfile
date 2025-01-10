# hash:sha256:d553c9ec1343b4d9c1237706f0a5a9f6aa5fd470f0076d4bef09fe06ea4e8540
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
    hdmf-zarr==0.10.0 \
    pynwb==2.8.3
