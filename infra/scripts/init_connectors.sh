#!/bin/sh

echo "Registering DynamoDB Sink Connector..."
curl -i -X POST -H "Content-Type: application/json" \
  -d @/config/dynamodb-sink.json \
  http://kafka-connect:8083/connectors

echo -e "\nRegistering Debezium Source Connector..."
curl -i -X POST -H "Content-Type: application/json" \
  -d @/config/debezium-source.json \
  http://kafka-connect:8083/connectors