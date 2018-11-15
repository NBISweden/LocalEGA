#!/bin/bash

set -e
set -x

[[ ! -s "/run/secrets/cega_connection" ]] && echo 'CEGA_CONNECTION secret is not present' 1>&2 && exit 1

# Initialization
rabbitmq-plugins enable --offline rabbitmq_federation
rabbitmq-plugins enable --offline rabbitmq_federation_management
rabbitmq-plugins enable --offline rabbitmq_shovel
rabbitmq-plugins enable --offline rabbitmq_shovel_management

cat > /etc/rabbitmq/rabbitmq.config <<EOF
%% -*- mode: erlang -*-
%%
[{rabbit,[{loopback_users, [ ] },
          {tcp_listeners, [ 5672 ] },
          {ssl_listeners, [ ] },
          {hipe_compile, false },
	  {default_vhost, "/"},
	  {disk_free_limit, "1GB"}]},
 {rabbitmq_management, [ { listener, [ { port, 15672 }, { ssl, false }] },
                         { load_definitions, "/etc/rabbitmq/defs.json"} ]}
].
EOF
chown rabbitmq:rabbitmq /etc/rabbitmq/rabbitmq.config
chmod 640 /etc/rabbitmq/rabbitmq.config


# Problem of loading the plugins and definitions out-of-orders.
# Explanation: https://github.com/rabbitmq/rabbitmq-shovel/issues/13
# Therefore: we run the server, with some default confs
# and then we upload the cega-definitions through the HTTP API

# We cannot add those definitions to defs.json (loaded by the
# management plugin. See /etc/rabbitmq/rabbitmq.config)
# So we use curl afterwards, to upload the extras definitions
# See also https://pulse.mozilla.org/api/

# dest-exchange-key is not set for the shovel, so the key is re-used.

# The user will be 'admin', with administrator rights. See below
cat > /etc/rabbitmq/defs-cega.json <<EOF
{"parameters":[{"value": {"src-uri": "amqp://",
			  "src-exchange": "cega",
			  "src-exchange-key": "#",
			  "dest-uri": "$(</run/secrets/cega_connection)",
			  "dest-exchange": "localega.v1",
			  "add-forward-headers": false,
			  "ack-mode": "on-confirm",
			  "delete-after": "never"},
            	"vhost": "/",
		"component": "shovel",
		"name": "to-CEGA"},
	       {"value": {"src-uri": "amqp://",
			   "src-exchange": "lega",
			   "src-exchange-key": "completed",
			   "dest-uri": "amqp://",
			   "dest-exchange": "cega",
			   "dest-exchange-key": "files.completed",
			   "add-forward-headers": false,
			   "ack-mode": "on-confirm",
			   "delete-after": "never"},
		"vhost": "/",
		"component": "shovel",
		"name": "CEGA-completion"},
	       {"value":{"uri":"$(</run/secrets/cega_connection)",
			 "ack-mode":"on-confirm",
			 "trust-user-id":false,
			 "queue":"v1.files"},
		"vhost":"/",
		"component":"federation-upstream",
		"name":"CEGA-files"},
	       {"value":{"uri":"$(</run/secrets/cega_connection)",
			 "ack-mode":"on-confirm",
			 "trust-user-id":false,
			 "queue":"v1.stableIDs"},
		"vhost":"/",
		"component":"federation-upstream",
		"name":"CEGA-ids"}],
 "policies":[{"vhost":"/",
              "name":"CEGA-files",
              "pattern":"files",
              "apply-to":"queues",
              "definition":{"federation-upstream":"CEGA-files"},
              "priority":0},
             {"vhost":"/",
              "name":"CEGA-ids",
              "pattern":"stableIDs",
              "apply-to":"queues",
              "definition":{"federation-upstream":"CEGA-ids"},
              "priority":0}]
}
EOF
chown rabbitmq:rabbitmq /etc/rabbitmq/defs-cega.json
chmod 640 /etc/rabbitmq/defs-cega.json

# And...cue music
chown -R rabbitmq /var/lib/rabbitmq

#rm -rf /run/secrets/cega_connection
exec "$@" # ie CMD rabbitmq-server
