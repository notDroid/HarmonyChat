FROM confluentinc/cp-server-connect:latest

# Install DynamoDB Sink
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-aws-dynamodb:latest

# Install Debezium PostgreSQL Source
RUN confluent-hub install --no-prompt debezium/debezium-connector-postgresql:latest
