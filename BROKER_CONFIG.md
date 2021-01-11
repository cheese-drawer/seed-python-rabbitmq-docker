This repo assumes the broker is an instance of the Docker Community maintained RabbitMQ image: [rabbitmq](registry.hub.docker.com/_/rabbitmq) with the broker exposed on port 5672, the management console on 15672, & the user authentication setup for a user named 'test' & a password of '69L88vette'. It can be initiated with the following command:

```
docker run -d \
  --hostname test-rabbitmq \
  --name test-rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=test \
  -e RABBITMQ_DEFAULT_PASS=69L88vette \
  rabbitmq:3-alpine
```
