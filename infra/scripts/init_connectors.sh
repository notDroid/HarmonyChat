#!/bin/sh

echo "Waiting for Kafka Connect REST API on ${CONNECT_URL}..."
while ! curl -s -f ${CONNECT_URL} > /dev/null; do
  sleep 5
done

echo "API is up. Registering DynamoDB Sink Connector..."
curl -i -X POST -H "Content-Type: application/json" \
  -d @/config/dynamodb-sink.json \
  ${CONNECT_URL} || echo "DynamoDB Sink already exists"

echo -e "\nRegistering Debezium Source Connector..."
curl -i -X POST -H "Content-Type: application/json" \
  -d @/config/debezium-source.json \
  ${CONNECT_URL} || echo "Debezium Source already exists"