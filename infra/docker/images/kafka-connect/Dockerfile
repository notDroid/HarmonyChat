# Pin to a specific Confluent Platform version
FROM confluentinc/cp-server-connect:7.5.3

# Pin plugins to explicit versions compatible with the base image
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-aws-dynamodb:1.4.1
RUN confluent-hub install --no-prompt debezium/debezium-connector-postgresql:2.4.2