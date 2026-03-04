import os
import urllib.request
import urllib.error

CONNECT_URL = os.getenv("KAFKA_CONNECT_URL", "http://kafka-connect:8083/connectors")
CONFIG_FILE = os.getenv("DYNAMODB_SINK_CONFIG_FILE", "infra/config/dynamodb-sink.json")

def register_connector():
    print("Registering DynamoDB Sink Connector...")
    with open(CONFIG_FILE, 'r') as f:
        config_data = f.read().encode('utf-8')
    
    req = urllib.request.Request(
        CONNECT_URL, 
        data=config_data, 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        print(f"Success! Connector registered: {response.read().decode('utf-8')}")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print("Connector already exists. Skipping creation.")
        else:
            print(f"Failed to register connector. HTTP {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print("An unexpected error occurred while registering the connector")
        raise

if __name__ == "__main__":
    register_connector()