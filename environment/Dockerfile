# hash:sha256:a3ade062bfcc1f7e0f55b32a310f914a7add908bad5c1054f166295766a60c85
FROM registry.codeocean.allenneuraldynamics.org/codeocean/jupyterlab:3.0.9-miniconda4.9.2-python3.8-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install -U --no-cache-dir \
    aind-data-access-api \
    pymongo \
    pynwb \
    ruamel-yaml
