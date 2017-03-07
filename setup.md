# Requirements

Maven 3 is used as build system for the projects

[Spring Tool Suite](https://spring.io/tools) (STS) is a free IDE that is
working well with project, Netbeans is an alternative


# Setup

In Uppsala/Sweden (NBISweden) we have made a fork of LocalEGA repos with submodules so you can clone all at once
```bash
git clone git@github.com:NBISweden/LocalEGA.git
cd LocalEGA
git submodule update --init
# Add elixir upstream
./add_elixir_remotes.sh
```

# Build

In Maven projects the config file `pom.xml`. The dependencies specified are
included in classpath and therefore beans are automatically created with
spring-boot, spring boot is figuring out what needs to be done by analysing
what is included in the classpath

Start class is specified in pom:
```xml
<start-class>eu.crg.ega.egabeacon.Application</start-class>
```


They should be built and installed in special order due to internal dependencies

```bash
for microservice in core-microservice common-jpa common-messaging \
        common-mongo config-microservice swagger-documentation-constants \
        worker-microservice session-microservice; do
    cd $microservice
    mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install
    cd ..
done
```

## Setup STS IDE

Download and install [Sprint Tool Suite (STS)](https://spring.io/tools)

## lombok

The Local_ega code is using lombok as a code generator for repetative code
e.g. getters, setters. Other examples of "lombok" annotations such as: `@Data`,
`@Builder`, `@AllArgsConstructor`, `@NoArgsConstructor`.

Install lombok in your STS directory, see https://projectlombok.org/

Import the repos (maven projects) into STS, choose File -> Open Project from File System...

In ega\_beacon If you get following error in STS:
```
Plugin execution not covered by lifecycle configuration: org.apache.servicemix.tooling:depends-maven-plugin:1.2:generate-depends-file
 (execution: generate-depends-file, phase: generate-resources)
```

Either Use the qick-fix problem in STS `Mark goal generate-depends-file as
ignored in eclipse preferences`  _OR_  Inside STS
`Window->proferences->Maven->Error/warnings->PluginNotCovered....`.


## Build profiles (for testing etc.)

There are specific profile files you can edit or create your own testing profile
e.g. the files:
```
src/main/resources/application-dev.properties
src/main/resources/application-dev.yml
```


## `SPRING_PROFILES` & properties

[PropertySource & Environment](http://blog.jamesdbloom.com/UsingPropertySourceAndEnvironment.html)

To make spring look for any application-dev.properties or application-dev.yml

```bash
SPRING_PROFILES_ACTIVE=dev mvn spring-boot:run
# or:
mvn spring-boot:run -Drun.jvmArguments="-Dspring.profiles.active=dev"
```

Another way is to compile with mvn and the run it with java -jar:

```bash
mvn clean compile package -Dspring.profiles.active="dev"
java -jar target/elixir-beacon.jar --spring.profiles.active=dev
```


# RabbitMQ

Local-ega is using RabbitMQ as message passing system between microservices.
We use a ready docker container for RabbitMQ. SSL keys and certificates are
needed for the https protocol of RabbitMQ.


## Generate certs and keys

Generate (for development) Keys, Certificates and CA Certificates (for rabbitmq ssl communication)
taken from the rabbitmq [ssl docs](https://www.rabbitmq.com/ssl.html).

```bash
export CERT_DIR=$HOME/localega/certs
mkdir $CERT_DIR
cd $CERT_DIR
mkdir testca
cd testca
mkdir certs private
chmod 700 private
echo 01 > serial
touch index.txt

# Now place the following in openssl.cnf within the testca directory we've just created
# see: https://www.rabbitmq.com/ssl.html
cd $CERT_DIR/testca
openssl req -x509 -config openssl.cnf -newkey rsa:2048 -days 365 -out cacert.pem -outform PEM -subj /CN=MyTestCA/ -nodes
openssl x509 -in cacert.pem -out cacert.cer -outform DER

# create servercert
cd $CERT_DIR
mkdir server
cd server
openssl genrsa -out key.pem 2048
openssl req -new -key key.pem -out req.pem -outform PEM \
  -subj /CN=$(hostname)/O=server/ -nodes
cd ../testca
openssl ca -config openssl.cnf -in ../server/req.pem -out \
  ../server/cert.pem -notext -batch -extensions server_ca_extensions
cd ../server
openssl pkcs12 -export -out keycert.p12 -in cert.pem -inkey key.pem -passout pass:MySecretPassword

# create clientcert
cd $CERT_DIR
mkdir client
cd client
openssl genrsa -out key.pem 2048
openssl req -new -key key.pem -out req.pem -outform PEM \
  -subj /CN=$(hostname)/O=client/ -nodes
cd ../testca
openssl ca -config openssl.cnf -in ../client/req.pem -out \
  ../client/cert.pem -notext -batch -extensions client_ca_extensions
cd ../client
openssl pkcs12 -export -out keycert.p12 -in cert.pem -inkey key.pem -passout pass:MySecretPassword

# generate java keystore
cd $CERT_DIR
keytool -import -alias server1 -file server/cert.pem -keystore store
```


## Install and configure rabbitMQ

Instead of installing software we use the already built [Docker
image](https://hub.docker.com/_/rabbitmq/)

We use 3-management image which is the rabbitmq v.3 server with management
plugin activated. We are remapping the ports to fit the local-ega settings and
map the local directory containing ssl keys and certificates.

NB: Change docker run parameters from -it to -d if you want to run it as a daemon.

```bash
export CERT_DIR=$HOME/localega/certs # From certs above
docker run -it --rm -p 5271:5671 -p 15671:15671 -v $CERT_DIR:/certs --hostname localhost --name rabbit-local-ega -e RABBITMQ_DEFAULT_VHOST=dev -e RABBITMQ_DEFAULT_USER=dev -e RABBITMQ_DEFAULT_PASS=W4BKsFgJCqu3Mhat -e RABBITMQ_SSL_CERT_FILE=/certs/server/cert.pem -e RABBITMQ_SSL_KEY_FILE=/certs/server/key.pem -e RABBITMQ_SSL_CA_FILE=/certs/testca/cacert.pem \rabbitmq:3-management
```


View RabbitMQ queues and exchanges in the rabbit managemnent webui at,
https://localhost:15671

The RabbitMQ exchanges and queues are defined from Java in microservices. In
Simpleservice for example they are of `Tuple` exchange type.


# MongoDB

MongoDB is used for users/sessions etc. And the test microservice,
simple-microservice, is using mongodb for storage.

An official docker image running [MongoDB](https://hub.docker.com/_/mongo/)

We are attaching a local directory as data directory

```bash
export MONGO_DIR=$HOME/localega/mongodb
docker run -it --rm -p 27017:27017 -v $MONGO_DIR:/data/db --name local-ega-mongo mongo:3 # --auth - it you want it:)
```

Connect to mongo for testing purposes with the mongo client - needs to be
installed locally.

```bash
mongo localhost:27017/dbname #(here specify password if you want)
```

Examplee mongo commands:
```
show dbs
use simple_dev
db.simpleThing.find()
```


# Swagger

Swagger dockerfile https://github.com/schickling/dockerfiles/tree/master/swagger-ui

Add allow cross-scripting origins to the microservices. You can add a
comma-separated white-list of domains to the
`src/main/resources/META-INF/corsFilter.properties` file. For example:

```
allowed.origins= http\://localhost\:9088,http\://localhost
```

## Swagger web ui

**NOT WORKING YET**

Start the swagger web ui

```bash
docker run -it --rm -p 9088:80 -e API_URL=http://localhost:8089/simpleservice/v1/api-docs schickling/swagger-ui
```

Should be at localhost:9088


# Login to the microservices

```bash
curl -X POST -d "username=user1" -d "password=user1" -d "loginType=INTERNAL" http://localhost:9200/sessionservice/v1/login
curl -X POST -d "username=user1" -d "password=user1" -d "loginType=INTERNAL" http://localhost:8089/simpleservice/v1/login

# Use sessionToken (from above):
curl -H "X-Token: 4ebc05f3-ccec-43a4-93c4-34b1866119f2" http://localhost:9200/sessionservice/v1/hello/anders

# status endpoint:
curl -H "X-Token: 4ebc05f3-ccec-43a4-93c4-34b1866119f2" http://localhost:9200/sessionservice/v1/status

# api-docs endpoint:
curl -H "X-Token: 4ebc05f3-ccec-43a4-93c4-34b1866119f2" http://localhost:9200/sessionservice/v1/api-docs

# test simpleservice
curl http://localhost:8089/simpleservice/v1/simple/hello
curl -X POST -d "name=user1" -d "age=10" -d "team=topteam" http://localhost:8089/simpleservice/v1/simple/simple_things
curl --data "param1=value1&param2=value2" http://localhost:8089/simpleservice/v1/simple/simple_things
```
