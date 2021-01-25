# Python microservice seed project

The following seed project can be used to set up any python-based service to run in Docker.
The project structure places the Docker & dev environment files at the root, with the python application inside `./app`:

```
.
|_ Dockerfile
|_ README
|_ app/
    |_ .python-version      # specify the supported python version here
    |_ requirements.txt     # recursively installs requirements/prod.txt, run
    |                       # `python -r requirements/dev.txt` for dev dependencies
    |_ requirements
    |   |_ dev.txt          # development only pip packages, not installed on Docker
    |   |_ prod.txt
    |_ src/                 # application code
    |   |_ worker/...           # lib to initialize & manage AMQP workers,
    |   |                       # probably don't need to touch this ever
    |   |                       # lib to initialize & manage AMQP workers,
    |   |_ server.py            # define service APIs here
    |   |_ lib.py               # example business logic, best to define it outside the API
    |_ tests/               # pytest tests
        |_ unit/                # unit tests go here, should mirror structure of ./app/src
        |   |_ lib.py               # easiest to not unit test your API as it has too many
        |                           # external, stateful & i/o bound dependencies
        |_ integration/         # for testing the API by actually interacting with it via a test
                                # RabbitMQ broker instance; tests defined here will be treated as
                                # the API contract

```

## Prerequisites

This seed assumes you have the following installed:

1. Docker
2. A RabbitMQ Broker

### Docker

Get Docker for your local machine by [going here](https://docs.docker.com/get-docker/) & following the instructions for your OS/desired setup.

### RabbitMQ Broker

The simplest way to get a Broker running on your local machine is to use the Docker Community maintained [rabbitmq](registry.hub.docker.com/_/rabbitmq) image. I prefer the alpine based version with the management console, allowing me to inspect the Broker in my browser. Install it with the following command:

```
docker run -d \
  --hostname test-rabbitmq \
  --name test-rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=test \
  -e RABBITMQ_DEFAULT_PASS={you make up a password here} \
  rabbitmq:3-management-alpine
```

This command does the following:

1. Runs the container in detached mode, allowing it to keep running in the background.
2. Names your Broker container 'test-rabbitmq'
3. Exposes the containers 5672 & 15672 ports. 5672 is necessary to allow anything on your local machine access to the broker to produce & consume messages. 15672 is necessary for you to access the management console at `localhost:15672`.
4. Changes the default user & password from the built-in defaults of 'guest' & 'guest' to 'test' & a password of your choice. This isn't strictly necessary, but makes for slightly better security in your dev environment.

Alternatively, you can use Docker Compose to orchestrate setting this broker container up with your service project container, allowing you to skip exposing port 5672 & define the Broker username & password w/ Docker Secrets, but that is outside the scope of this README for now.

## Installation

To use this to seed a new project, just download a release, decompress it, and start modifying as needed.
Alternatively, clone this repo to your local machine, then delete the `.git/` directory and init a new repo with `git init`.

To run run the service, first build your image using `docker build -t {YOUR_IMAGE_NAME_HERE} .`.
When built, you can then start the service using the following `docker run` command:

```
docker run \
  -d \
  --name {pick a container name, or omit this flag} \
  --env BROKER_HOST={your local development RabbitMQ Broker host name} \
  --env BROKER_USER={your local development RabbitMQ Broker username} \
  --env BROKER_PASS={your local development RabbitMQ Broker password} \
  --network host \
  -v {full path to project directory}/app:/app \
  {YOUR_IMAGE_NAME_HERE}
```

This `run` command does the following:

1. Starts the container in detached mode, running it in the background
2. Tells the application where to find your development RabbitMQ broker & how to connect so you can test it
3. Uses your host machine's network to simplify Docker networking for development purposes
5. Mounts the `./app` directory as a volume on the container, allowing you to make changes to the application without rebuilding the image
6. Runs the image you named in the previous `docker build ...` command

Alternatively, you can use Docker Compose to manage both this service container & your RabbitMQ broker container, allowing you to just give the RabbitMQ container name as the host name to BROKER_HOST & skip giving this container your full host network.

## Usage

With your seed project container running & a volume mapped to your working directory's `./app` directory, you can start modifying the contents of `./app` all you want. To see the effect of your changes on the container, just stop it & restart it with `docker stop {your container name}` & `docker start {your container name}`, then try sending messages to the API you've defined & inspect the service's logs with `docker logs {your container name}`.
