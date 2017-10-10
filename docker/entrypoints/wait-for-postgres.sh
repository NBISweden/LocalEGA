#!/bin/bash

set -e

cmd="$@"

export PGPASSWORD=$POSTGRES_PASSWORD

until psql -U $POSTGRES_USER -h ega_db -c "select 1"; do sleep 1; done

>&2 echo "Postgres is up - executing command"
exec $cmd