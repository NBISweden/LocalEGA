FROM nbisweden/ega-os:latest AS build-base

#################################################
##
## Upgrade CentOS 7, and install Python 3.6
##
#################################################

RUN yum -y install git gcc make bzip2 curl \
    zlib-devel bzip2-devel unzip openssl \
    python36u python36u-devel python36u-pip && \
    cp /usr/bin/python3.6 /usr/local/bin/

RUN [[ -e /lib64/libpython3.6m.so ]] || ln -s /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so

RUN pip3.6 install --upgrade pip && \
    pip3.6 install --no-cache-dir PyYaml

#################################################
##
## Install GOSU
##
#################################################

ENV GOSU_VERSION 1.10
ENV GPG_KEYS B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN set -ex && \
    curl -Lo /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-amd64" && \
    curl -Lo /tmp/gosu.asc "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-amd64.asc"

# verify the signature
RUN export GNUPGHOME="$(mktemp -d)" && \
    (gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEYS" \
    || gpg --keyserver pgp.mit.edu --recv-keys "$GPG_KEYS" \
    || gpg --keyserver keyserver.pgp.com --recv-keys "$GPG_KEYS") && \
    gpg --keyserver hkps://hkps.pool.sks-keyservers.net --recv-keys  && \
    gpg --batch --verify /tmp/gosu.asc /usr/local/bin/gosu && \
    rm -r "$GNUPGHOME" /tmp/gosu.asc && \
    chmod +x /usr/local/bin/gosu

#################################################
##
## Install LocalEGA stuff
##
#################################################

ARG checkout=master
RUN git clone https://github.com/NBISweden/LocalEGA.git /root/LocalEGA && \
    cd /root/LocalEGA && \
    git checkout ${checkout}

RUN git clone https://github.com/NBISweden/LocalEGA-cryptor.git /root/LocalEGA-cryptor && \
    pip3.6 install -r /root/LocalEGA-cryptor/requirements.txt

RUN pip3.6 install -r /root/LocalEGA/requirements.txt && \
    pip3.6 install /root/LocalEGA

FROM nbisweden/ega-os:latest

LABEL maintainer "EGA System Developers"

WORKDIR /

RUN groupadd -r lega && \
    useradd -M -r -g lega lega

COPY --from=build-base /usr/lib/python3.6 /usr/lib/python3.6

COPY --from=build-base /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so.1.0

COPY --from=build-base /usr/local/bin /usr/local/bin
