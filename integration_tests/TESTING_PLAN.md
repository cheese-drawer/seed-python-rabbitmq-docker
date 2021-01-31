# Testing plan

## Goals

Integration testing should prove the following:

1. The service is buildable using the Dockerfile contained at ./Dockerfile per any
  instructions provided in the README
2. The service is runnable using Docker per any instructions provided in the README
3. Each endpoint in the service's Request/Reply API returns the expected data when
  sent a request
3. For any event that should cause the service to publish a message on the
  Service 2 Service API, the expected message is published

## Setup

1. Setup a test broker & set it's host name, port, user, & password as the BROKER_HOST,
  BROKER_PORT, BROKER_USER, & BROKER_PASS environment variables
2. Setup a test Database via & set it's connection info via environment variables
  FIXME: these environment variables still need names

## Run

Execute a series of requests & assert the returned response against the expectation.

Each test should consider the following:

- The "normal" case
- Edge cases, including:

  - Null requests
  - Unexpected data in the request

- Expected side effects of sending a Request to a Request/Reply endpoint, expressed
  as an outbound message from the service on the internal Service 2 Service API
- Expected changes to the database when an inbound message is received on an internal
  Service 2 Service API endpoint

The following is behavior of RabbitMQ & does not need tested:

- What response is received (or not received) when a message is sent to a non-existent endpoint
- What response is expected when the connection fails

## Teardown

1. Stop & reset the test database
2. Stop & kill the test Broker (making sure to delete any configuration it had stored on a volume)
