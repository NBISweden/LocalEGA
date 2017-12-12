FROM rabbitmq:management
LABEL maintainer "Frédéric Haziza, NBIS"

RUN apt-get update && \
    apt-get install -y curl netcat && \
    rm -rf /var/lib/apt/lists/*

RUN rabbitmq-plugins enable --offline rabbitmq_federation && \
    rabbitmq-plugins enable --offline rabbitmq_federation_management && \
    rabbitmq-plugins enable --offline rabbitmq_shovel && \
    rabbitmq-plugins enable --offline rabbitmq_shovel_management

# See inside the entrypoint for the reason
COPY entrypoint.sh /usr/bin/ega-entrypoint.sh
RUN chmod +x /usr/bin/ega-entrypoint.sh
ENTRYPOINT ["/usr/bin/ega-entrypoint.sh"]
