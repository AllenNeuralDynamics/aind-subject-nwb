# hash:sha256:39ff8300f79803f47c6ec828bc89d5ab2fa315e68b3a98cd9829e837b48f75e4
FROM registry.codeocean.allenneuraldynamics.org/codeocean/jupyterlab:3.6.1-miniconda4.12.0-python3.9-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install -U --no-cache-dir \
    aind-data-access-api==0.6.1 \
    boto3==1.28.72 \
    hdmf-zarr==0.4.0 \
    pynwb==2.5.0
