FROM nbisweden/ega-os:latest as build

RUN yum -y install git gcc make bzip2 curl ${DEV_PACKAGES} \
    zlib-devel bzip2-devel unzip wget dpkg \
    openssl python36u python36u-devel python36u-pip \
    autoconf patch openssl-devel pam-devel libcurl-devel \
    nss-tools readline-devel libedit-devel


#################################################
##
## Install GOSU
##
#################################################

ENV GOSU_VERSION 1.10
ENV GPG_KEYS B42F6819007F00F88E364FD4036A9C25BF357DD4
RUN set -ex && \
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')" && \
    wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}" && \
    wget -O /tmp/gosu.asc "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${dpkgArch}.asc"

# verify the signature
RUN export GNUPGHOME="$(mktemp -d)" && \
    (gpg --keyserver ha.pool.sks-keyservers.net --recv-keys "$GPG_KEYS" \
    || gpg --keyserver pgp.mit.edu --recv-keys "$GPG_KEYS" \
    || gpg --keyserver keyserver.pgp.com --recv-keys "$GPG_KEYS") && \
    gpg --keyserver hkps://hkps.pool.sks-keyservers.net --recv-keys  && \
    gpg --batch --verify /tmp/gosu.asc /usr/local/bin/gosu && \
    rm -r "$GNUPGHOME" /tmp/gosu.asc && \
    chmod +x /usr/local/bin/gosu

##
## Install SQLite 3.24
##
ARG SQLITE_VERSION=3240000
RUN cd && curl -O https://sqlite.org/2018/sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    tar xzf sqlite-autoconf-${SQLITE_VERSION}.tar.gz && \
    cd sqlite-autoconf-${SQLITE_VERSION} && \
    ./configure && \
    make && make install

RUN git clone https://github.com/NBISweden/LocalEGA-auth.git /root/LocalEGA-auth && \
    mkdir -p /usr/local/lib/ega && \
    cd /root/LocalEGA-auth/src && \
    make clean debug3 && make install

ARG OPENSSH_DIR=/opt/openssh
ARG SSHD_UID=74
ARG SSHD_GID=74
ARG OPENSSH_TAG=V_7_8_P1

RUN git clone --branch ${OPENSSH_TAG} git://anongit.mindrot.org/openssh.git /root/openssh && \
    cd /root/openssh && \
    autoreconf && \
    ./configure \
    --prefix=${OPENSSH_DIR} \
    --with-privsep-path=/var/empty/sshd \
    --with-privsep-user=sshd \
    --with-ssl-engine \
    --disable-strip \
    --without-smartcard \
    --with-pam \
    --without-selinux \
    --without-kerberos5 \
    --with-libedit

COPY notify_cega.patch /root/openssh/notify_cega.patch

RUN cd /root/openssh && \
    patch -p0 < notify_cega.patch && \
    make && make install

RUN rm -f /etc/ssh/ssh_host_{rsa,dsa,ecdsa,ed25519}_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t rsa     -N '' -f /etc/ssh/ssh_host_rsa_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t dsa     -N '' -f /etc/ssh/ssh_host_dsa_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t ecdsa   -N '' -f /etc/ssh/ssh_host_ecdsa_key && \
    ${OPENSSH_DIR}/bin/ssh-keygen -t ed25519 -N '' -f /etc/ssh/ssh_host_ed25519_key

# Install the notification system

# These are enough
RUN pip3.6 install --upgrade pip && \
    pip3.6 install pika==0.12.0 uvloop

ARG checkout=master
RUN git clone https://github.com/NBISweden/LocalEGA.git /root/LocalEGA && \
    cd /root/LocalEGA && \
    git checkout ${checkout} && cd && \
    pip3.6 -v install --install-option="--prefix=/usr/local/bin/" /root/LocalEGA

#################################################
##
## Create production container
##
#################################################

FROM nbisweden/ega-os:latest

LABEL maintainer "EGA System Developers"

RUN yum -y install libedit && \
    yum clean all && rm -rf /var/cache/yum

RUN groupadd -r lega && \
    useradd -M -r -g lega lega

EXPOSE 9000
VOLUME /ega/inbox

WORKDIR /

COPY --from=build /usr/lib/python3.6/ /usr/lib/python3.6/

COPY --from=build /lib64/libpython3.6m.so.1.0 /lib64/libpython3.6m.so.1.0

COPY --from=build /usr/local/bin/ /usr/local/bin/

COPY --from=build /usr/local/lib/ /usr/local/lib/

COPY --from=build /opt/openssh/sbin/sshd /opt/openssh/sbin/ega

COPY --from=build /etc/ssh/ /etc/ssh/

COPY pam.ega /etc/pam.d/ega

COPY sshd_config /etc/ega/sshd_config

COPY entrypoint.sh /usr/local/bin/entrypoint.sh

RUN echo '/usr/local/lib/ega' >> /etc/ld.so.conf.d/ega.conf && \
    sed -i -e 's/^passwd:\(.*\)files/passwd:\1files ega/' /etc/nsswitch.conf && \
    sed -i -e '/sshd/ d' /etc/passwd && \
    echo "sshd:x:74:74:Privilege-separated SSH:/var/empty/sshd:/sbin/nologin" >> /etc/passwd && \
    echo 'Welcome to Local EGA' > /ega/banner && \
    mkdir -p /var/empty/sshd && chmod 700 /var/empty/sshd && \
    getent group ssh_keys >/dev/null || groupadd -r ssh_keys || : && \
    getent group sshd || groupadd -g 74 -r sshd && \
    chmod 755 /usr/local/bin/entrypoint.sh && \
    ldconfig -v

ENTRYPOINT ["entrypoint.sh"]
