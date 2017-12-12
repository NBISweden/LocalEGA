#!/bin/bash

#set -e

[[ -z "${INSTANCE}" ]] && echo 'Environment INSTANCE is empty' 1>&2 && exit 1
[[ -z "${CEGA_MQ_PASSWORD}" ]] && echo 'Environment CEGA_MQ_PASSWORD is empty' 1>&2 && exit 1

# Problem of loading the plugins and definitions out-of-orders.
# Therefore: we run the server, empty
# and then we upload the definitions through the HTTP API

# We cannot use that in /etc/rabbitmq/rabbitmq.config
# %% -*- mode: erlang -*-
# %%
# [{rabbit,[{loopback_users, [ ] },
# 	  {default_vhost, "/"},
# 	  {default_user,  "guest"},
# 	  {default_pass,  "guest"},
# 	  {default_permissions, [".*", ".*",".*"]},
# 	  {default_user_tags, [administrator]},
# 	  {disk_free_limit, "1GB"}]},
#  {rabbitmq_management, [ {load_definitions, "/etc/rabbitmq/defs.json"} ]}
# ].

# cat > /etc/rabbitmq/rabbitmq.config <<EOF
# [
#         { rabbit, [
#                 { loopback_users, [ ] },
#                 { tcp_listeners, [ 5672 ] },
#                 { ssl_listeners, [ ] },
#                 { hipe_compile, false }
#         ] },
#         { rabbitmq_management, [ { listener, [
#                 { port, 15672 },
#                 { ssl, false }
#         ] } ] }
# ].
# EOF

# For the moment, still using guest:guest
cat > /etc/rabbitmq/defs.json <<EOF
{"rabbit_version":"3.6.12",
 "users":[{"name":"guest","password_hash":"4tHURqDiZzypw0NTvoHhpn8/MMgONWonWxgRZ4NXgR8nZRBz","hashing_algorithm":"rabbit_password_hashing_sha256","tags":"administrator"}],
 "vhosts":[{"name":"/"}],
 "permissions":[{"user":"guest","vhost":"/","configure":".*","write":".*","read":".*"}],
 "parameters":[{"value":{"src-uri":"amqp://",
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
 "global_parameters":[{"name":"cluster_name","value":"rabbit@localhost"}],
 "policies":[{"vhost":"/","name":"CEGA","pattern":"files","apply-to":"queues","definition":{"federation-upstream":"CEGA"},"priority":0}],
"queues":[{"name":"archived",   "vhost":"/","durable":true,"auto_delete":false,"arguments":{}},
	  {"name":"staged",     "vhost":"/","durable":true,"auto_delete":false,"arguments":{}},
	  {"name":"files",      "vhost":"/","durable":true,"auto_delete":false,"arguments":{}},
	  {"name":"cega.errors","vhost":"/","durable":true,"auto_delete":false,"arguments":{}},
	  {"name":"verified",   "vhost":"/","durable":true,"auto_delete":false,"arguments":{}}],
 "exchanges":[{"name":"lega","vhost":"/","type":"topic","durable":true,"auto_delete":false,"internal":false,"arguments":{}}],
 "bindings":[{"source":"lega","vhost":"/","destination":"archived","destination_type":"queue","routing_key":"lega.archived","arguments":{}},
	     {"source":"lega","vhost":"/","destination":"cega.errors","destination_type":"queue","routing_key":"lega.error.user","arguments":{}},
	     {"source":"lega","vhost":"/","destination":"staged","destination_type":"queue","routing_key":"lega.staged","arguments":{}},
	     {"source":"lega","vhost":"/","destination":"verified","destination_type":"queue","routing_key":"lega.verified","arguments":{}}]
}
EOF
chown rabbitmq:rabbitmq /etc/rabbitmq/defs.json
chmod 640 /etc/rabbitmq/defs.json

# And...cue music
rabbitmq-server &
PID=$!

# Wait until the server is ready (on the management port)
#until nc -4 --send-only 127.0.0.1 15672 </dev/null &>/dev/null; do sleep 1; done
until nc -z 127.0.0.1 15672; do sleep 1; done
# $1 is CMD
curl -X POST -u guest:guest -H "Content-Type: application/json" --data @/etc/rabbitmq/defs.json http://127.0.0.1:15672/api/definitions

wait ${PID}
