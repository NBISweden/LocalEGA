#!/bin/bash

set -e
set -x

[[ -z "${INSTANCE}" ]] && echo 'Environment INSTANCE is empty' 1>&2 && exit 1
[[ -z "${CEGA_MQ_PASSWORD}" ]] && echo 'Environment CEGA_MQ_PASSWORD is empty' 1>&2 && exit 1

# Problem of loading the plugins and definitions out-of-orders.
# Therefore: we run the server, empty
# and then we upload the definitions through the HTTP API

# We cannot add those definitions to defs.json (loaded by the
# management plugin. See /etc/rabbitmq/rabbitmq.config)
# So we use curl afterwards, to upload the extras definitions
# See also https://pulse.mozilla.org/api/

# For the moment, still using guest:guest
cat > /etc/rabbitmq/defs-cega.json <<EOF
{"parameters":[{"value":{"src-uri":"amqp://",
			 "src-exchange":"lega",
			 "src-exchange-key":"lega.error.user",
			 "dest-uri":"amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega_mq:5672/${INSTANCE}",
			 "dest-exchange":"localega.v1",
			 "dest-exchange-key":"${INSTANCE}.errors",
			 "add-forward-headers":false,
			 "ack-mode":"on-confirm",
			 "delete-after":"never"},
		"vhost":"/",
		"component":"shovel",
		"name":"CEGA-errors"},
	       {"value":{"src-uri":"amqp://",
			 "src-exchange":"lega",
			 "src-exchange-key":"lega.completed",
			 "dest-uri":"amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega_mq:5672/${INSTANCE}",
			 "dest-exchange":"localega.v1",
			 "dest-exchange-key":"${INSTANCE}.completed",
			 "add-forward-headers":false,
			 "ack-mode":"on-confirm",
			 "delete-after":"never"},
		"vhost":"/",
		"component":"shovel",
		"name":"CEGA-completion"},
	       {"value":{"uri":"amqp://cega_${INSTANCE}:${CEGA_MQ_PASSWORD}@cega_mq:5672/${INSTANCE}",
			 "ack-mode":"on-confirm",
			 "trust-user-id":false,
			 "queue":"${INSTANCE}.v1.commands.file"},
		"vhost":"/",
		"component":"federation-upstream",
		"name":"CEGA"}],
 "policies":[{"vhost":"/","name":"CEGA","pattern":"files","apply-to":"queues","definition":{"federation-upstream":"CEGA"},"priority":0}]
}
EOF
chown rabbitmq:rabbitmq /etc/rabbitmq/defs-cega.json
chmod 640 /etc/rabbitmq/defs-cega.json

# And...cue music
chown -R rabbitmq /var/lib/rabbitmq
"$@" & # ie CMD rabbitmq-server
PID=$!
trap "kill ${PID}; exit 1" INT

# Wait until the server is ready (on the management port)
#until nc -4 --send-only 127.0.0.1 15672 </dev/null &>/dev/null; do sleep 1; done
until nc -z 127.0.0.1 15672; do sleep 1; done
ROUND=30
until curl -X POST -u guest:guest -H "Content-Type: application/json" --data @/etc/rabbitmq/defs-cega.json http://127.0.0.1:15672/api/definitions || ((ROUND<0)); do sleep 1; $((ROUND--)); done

wait ${PID}
