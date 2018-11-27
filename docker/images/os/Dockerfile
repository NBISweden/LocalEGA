FROM centos:7.5.1804 AS base

RUN cd /tmp/ && curl -OL https://github.com/CentOS/sig-cloud-instance-images/raw/CentOS-7.5.1804/docker/centos-7-docker.tar.xz

RUN	mkdir -p /tmp/root && tar xJf /tmp/centos-7-docker.tar.xz -C /tmp/root

FROM scratch

LABEL maintainer "NBIS System Developers"

COPY --from=base /tmp/root/ /

RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm && \
    yum -y install epel-release && \
    yum -y update && yum clean all && \
    rm -rf /var/cache/yum
