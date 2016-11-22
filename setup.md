```bash
# Requirements
# Maven 3 is used as build system for the projects
#
# STS is a free IDE that is working well with project, Netbeans is an alternative


# create directory local_ega
mkdir local_ega
cd local_ega

# Clone all repos of interest into folder local_ega
# Libraries --
# Constants to shown in swagger
git clone https://github.com/elixir-europe/swagger-documentation-constants
# Core component of all microservices
git clone https://github.com/elixir-europe/core-microservice
# Core part related to JPA
git clone https://github.com/elixir-europe/common-jpa
# Core part related to Mongo
git clone https://github.com/elixir-europe/common-mongo
# Core part related to messaging
git clone https://github.com/elixir-europe/common-messaging
# Microservices --
# Config microservice
git clone https://github.com/elixir-europe/config-microservice
# Session microservice, it uses an authprovider that will validate any user and password
git clone https://github.com/elixir-europe/session-microservice
# Worker microservice
git clone https://github.com/elixir-europe/worker-microservice

# In Uppsala/Sweden (NBISweden) we have made a fork of LocalEGA repos with submodules so you can clone all at once
git clone git@github.com:NBISweden/LocalEGA.git

#
# BUILD
#

# In Maven projects the config file pom.xml
# The dependencies specified are included in classpath and therefore beans are automatically
# created with spring-boot, spring boot is figuring out what needs to be done by analysing
# what is included in the classpath

# Start class is specified in pom:
<start-class>eu.crg.ega.egabeacon.Application</start-class>


# They should be built and installed in special order due to internal dependencies
cd core-microservice
mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install
cd ..
cd common-jpa
mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install
cd ..
cd common-messaging
mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install
cd ..
cd common-mongo
mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install
cd ..
cd config-microservice
mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install
cd ..
cd swagger-documentation-constants
mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install
cd ..
cd worker-microservice
mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install
cd ..
cd session-microservice
mvn -DargLine="-Dspring.profiles.active=dev" clean compile package install

#
# Setup STS IDE
#

# Download and install STS (Spring Tools Suite)

# lombok
# The Local_ega code is using lombok as a code generator for repetative code e.g. getters, setters
# Other examples of "lombok" annotations such as: @Data, @Builder, @AllArgsConstructor, @NoArgsConstructor
# Install lombok in your STS directory, see https://projectlombok.org/

# Import the repos (maven projects) into STS, choose File -> Open Project from File System...

# In ega_beacon If you get following error in STS:
Plugin execution not covered by lifecycle configuration: org.apache.servicemix.tooling:depends-maven-plugin:1.2:generate-depends-file
 (execution: generate-depends-file, phase: generate-resources)
# Use the qick-fix problem in STS "Mark goal generate-depends-file as ignored in eclipse preferences"
#
# OR:
#
# Inside STS Window->proferences->Maven->Error/warnings->PluginNotCovered....



#
# More about BUILDING
#
# 
# There are specific profile files you can edit or create your own testing profile
# e.g. the files:
# /src/main/resources/application-dev.properties
# /src/main/resources/application-dev.yml
#
# A little bit about SPRING_PROFILES & properties
#
# PropertySource & Environment 
# http://blog.jamesdbloom.com/UsingPropertySourceAndEnvironment.html

# To run project with profile specified:
# this will make spring automatically look for any application-dev.properties or application-dev.yml

SPRING_PROFILES_ACTIVE=dev mvn spring-boot:run
# or:
mvn spring-boot:run -Drun.jvmArguments="-Dspring.profiles.active=dev"

# Another way is to compile with mvn and the run it with java -jar:
mvn clean compile package -Dspring.profiles.active="dev"
java -jar target/elixir-beacon.jar --spring.profiles.active=dev


#
#
# RabbitMQ Local_ega is using RabbitMQ as message passing system between microservices
#
#

# We use a ready docker container for RabbitMQ

# SSL keys and certificates are needed for the https protocol of RabbitMQ

# Generate (for development) Keys, Certificates and CA Certificates (for rabbitmq ssl communication)
#
# The code below is described in the docs/tutorial: https://www.rabbitmq.com/ssl.html

mkdir /certs
cd /certs
mkdir testca
cd testca
mkdir certs private
chmod 700 private
echo 01 > serial
touch index.txt

# Now place the following in openssl.cnf within the testca directory we've just created
# see: https://www.rabbitmq.com/ssl.html
cd /certs/testca
openssl req -x509 -config openssl.cnf -newkey rsa:2048 -days 365 -out cacert.pem -outform PEM -subj /CN=MyTestCA/ -nodes
openssl x509 -in cacert.pem -out cacert.cer -outform DER

# create servercert
cd /certs
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
cd /certs
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
cd /certs
keytool -import -alias server1 -file server/cert.pem -keystore store

#
# (Install and configure rabbitMQ)
# Instead of installing software we are already built Docker image
# https://hub.docker.com/_/rabbitmq/

# We use 3-management image (this is rabbitmq v.3 server with management plugin activated)
# (change docker run parameters -it to -d if you want to run it as a daemon
# We are remapping the ports to fit the local-ega settings and mapping a local directory containing ssl keys and certificates
docker run -it --rm -p 5271:5671 -p 15671:15671 -v /certs:/certs --hostname localhost --name rabbit-local-ega -e RABBITMQ_DEFAULT_VHOST=dev -e RABBITMQ_DEFAULT_USER=dev -e RABBITMQ_DEFAULT_PASS=W4BKsFgJCqu3Mhat -e RABBITMQ_SSL_CERT_FILE=/certs/server/cert.pem -e RABBITMQ_SSL_KEY_FILE=/certs/server/key.pem -e RABBITMQ_SSL_CA_FILE=/certs/testca/cacert.pem \rabbitmq:3-management

# View RabbitMQ queues and exchanges in the rabbit managemnent webui
https://localhost:15671

# The RabbitMQ exchanges and queues are defined from Java in microservices.  (in Simpleservice they are of "Tuple" exchange type)


#
#
# MongoDB (this is used for users/sessions etc.) - also the test microservice
# simple-microservice is using mongodb for storage
#
#

#
# An official docker image running mongoDB
# mongodb https://hub.docker.com/_/mongo/

# We are attaching a local directory as data directory
docker run -it --rm -p 27017:27017 -v /mongo/localega-datadir:/data/db --name local-ega-mongo mongo:3 # --auth - it you want it:)

# connect to mongo for testing purposes (with mongo client - needs to be installed)
mongo localhost:27017/dbname #(here specify password if you want)

# examplee mongo commands:
show dbs
use simple_dev
db.simpleThing.find()


#
#
# Swagger
#
#

# swagger dockerfile
https://github.com/schickling/dockerfiles/tree/master/swagger-ui

# add allow cross-scripting origins to the microservices
# You can add the domain you want in the file src/main/resources/META-INF/corsFilter.properties a list of comma separated values
allowed.origins= http\://localhost\:9088,http\://localhost

# start swagger web ui
docker run -it --rm -p 9088:80 -e API_URL=http://localhost:8089/simpleservice/v1/api-docs schickling/swagger-ui

# Swagger web ui
#
# NOT WORKING YET!!!
#
localhost:9088


# login to microservice
curl -X POST -d "username=user1" -d "password=user1" -d "loginType=INTERNAL" http://localhost:9200/sessionservice/v1/login
curl -X POST -d "username=user1" -d "password=user1" -d "loginType=INTERNAL" http://localhost:8089/simpleservice/v1/login

# Use sessionToken:
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








