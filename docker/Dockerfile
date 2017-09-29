FROM ubuntu:17.04

MAINTAINER https://github.com/dtitov

# Install required tools 
RUN apt update && apt install wget curl nano mc git openssl docker.io -yq --no-install-recommends

# Install GPG 2.2
WORKDIR gpg_installation
RUN apt update && apt -y install libgnutls-dev bzip2 make gettext texinfo gnutls-bin libgnutls28-dev build-essential libbz2-dev zlib1g-dev libncurses5-dev libsqlite3-dev libldap2-dev || apt -y install libgnutls28-dev bzip2 make gettext texinfo gnutls-bin build-essential libbz2-dev zlib1g-dev libncurses5-dev libsqlite3-dev libldap2-dev
RUN wget -c https://www.gnupg.org/ftp/gcrypt/libgpg-error/libgpg-error-1.27.tar.gz && \
wget -c https://www.gnupg.org/ftp/gcrypt/libgcrypt/libgcrypt-1.8.1.tar.gz && \
wget -c https://www.gnupg.org/ftp/gcrypt/libassuan/libassuan-2.4.3.tar.bz2 && \
wget -c https://www.gnupg.org/ftp/gcrypt/libksba/libksba-1.3.5.tar.bz2 && \
wget -c https://www.gnupg.org/ftp/gcrypt/npth/npth-1.5.tar.bz2 && \
wget -c https://www.gnupg.org/ftp/gcrypt/pinentry/pinentry-1.0.0.tar.bz2 && \
wget -c https://www.gnupg.org/ftp/gcrypt/gnupg/gnupg-2.2.1.tar.bz2 && \
tar -xzf libgpg-error-1.27.tar.gz && \
tar -xzf libgcrypt-1.8.1.tar.gz && \
tar -xjf libassuan-2.4.3.tar.bz2 && \
tar -xjf libksba-1.3.5.tar.bz2 && \
tar -xjf npth-1.5.tar.bz2 && \
tar -xjf pinentry-1.0.0.tar.bz2 && \
tar -xjf gnupg-2.2.1.tar.bz2 && \
cd libgpg-error-1.27/ && ./configure && make && make install && cd ../ && \
cd libgcrypt-1.8.1 && ./configure && make && make install && cd ../ && \
cd libassuan-2.4.3 && ./configure && make && make install && cd ../ && \
cd libksba-1.3.5 && ./configure && make && make install && cd ../ && \
cd npth-1.5 && ./configure && make && make install && cd ../ && \
cd pinentry-1.0.0 && ./configure --enable-pinentry-curses --disable-pinentry-qt4 && \
make && make install && cd ../ && \
cd gnupg-2.2.1 && ./configure && make && make install && \
echo "/usr/local/lib" > /etc/ld.so.conf.d/gpg2.conf && ldconfig -v

# Generate GPG stuff
WORKDIR ../lega_setup/gpg_home
RUN echo "%echo Generating a basic OpenPGP key \n\
Key-Type: RSA \n\
Key-Length: 4096 \n\
Name-Real: EGA Sweden \n\
Name-Comment: @NBIS \n\
Name-Email: ega@nbis.se \n\
Expire-Date: 0 \n\
Passphrase: passphrase \n\
# Do a commit here, so that we can later print "done" :-) \n\
%commit \n\
%echo done" >> gen_key && gpg --homedir . --batch --generate-key gen_key


# Generate RSA stuff
WORKDIR ../rsa_home
RUN openssl genpkey -algorithm RSA -out rsa.sec -pkeyopt rsa_keygen_bits:2048 && openssl rsa -pubout -in rsa.sec -out rsa.pub

# Generate SSL stuff
WORKDIR ../ssl_home
RUN openssl req -x509 -newkey rsa:2048 -keyout ssl.key -nodes -out ssl.cert -sha256 -days 1000 -subj "/C=NO/ST=Oslo/L=Oslo/O=UiO/OU=IFI/CN=test"

# Generate MD5 stuff
WORKDIR ../md5_home
RUN echo "Algorithm: MD5\nSalt: xyz\nPassword: hello\n$(openssl passwd -1 -salt xyz hello)" >> password_hash

# Fake EGA user
WORKDIR ../cega_users
RUN echo "---\npassword_hash: $(openssl passwd -1 -salt xyz hello)" >> john.yml

# Populate configs
WORKDIR ..
RUN echo "[DEFAULT] \n\
active_master_key = 1 \n\
[master.key.1] \n\
seckey = /etc/ega/rsa/sec.pem \n\
pubkey = /etc/ega/rsa/pub.pem \n\
passphrase = passphrase" >> keys.conf
RUN echo "[DEFAULT] \n\
log = debug \n\
[ingestion] \n\
gpg_cmd = /usr/local/bin/gpg --homedir ~/.gnupg --decrypt %(file)s \n\
vhost = test \n\
heartbeat = 0 \n\
[db] \n\
host = ega_db \n\
username = user \n\
password = password \n\
[cega.broker] \n\
host = cega_mq \n\
username = test " >> conf.ini

# Populate env-settings
WORKDIR .env.d
RUN echo "POSTGRES_USER=user\nPOSTGRES_PASSWORD=password" >> db && echo "GPG_PASSPHRASE=passphrase" >> gpg
WORKDIR ..
RUN echo "COMPOSE_PROJECT_NAME=ega \n\
COMPOSE_FILE=ega.yml \n\
CODE=../src \n\
CONF=./conf.ini \n\
KEYS=./keys.conf \n\
SSL_CERT=./ssl_home/ssl.cert \n\
SSL_KEY=./ssl_home/ssl.key \n\
RSA_SEC=./rsa_home/sec.pem \n\
RSA_PUB=./rsa_home/pub.pem \n\
GPG_HOME=./gpg_home \n\
CEGA_USERS=./cega_users" >> .env

RUN mkdir ../configuration

CMD echo "password = ${password}" >> conf.ini && cp -r . ../configuration 