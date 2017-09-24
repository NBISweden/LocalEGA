#!/bin/bash

set -e

chown root:ega /ega/inbox
chmod 750 /ega/inbox
chmod g+s /ega/inbox # setgid bit

pushd /root/ega/auth
make
make install
popd

ldconfig -v

mkdir -p /etc/ega
cat > /etc/ega/auth.conf <<EOF
debug = ok_why_not

##################
# Databases
##################
db_connection = host=172.18.0.2 port=5432 dbname=lega user=postgres password=mysecretpassword connect_timeout=1 sslmode=disable

#enable_rest = no
rest_endpoint = https://ega.crg.eu/users/%s

##################
# NSS Queries
##################
nss_user_entry = SELECT elixir_id,'x',1000,1000,'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users WHERE elixir_id = $1 LIMIT 1

##################
# PAM Queries
##################
pam_auth = SELECT password_hash FROM users WHERE elixir_id = $1 LIMIT 1
pam_acct = SELECT user_expired($1)
EOF

echo "Waiting for database"
until nc -4 --send-only ega_db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the SFTP server"
exec /usr/sbin/sshd -D -e
