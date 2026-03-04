from init_dynamodb_sink import register_connector
from init_dynamodb_tables import init_db

if __name__ == "__main__":
    init_db()    
    register_connector()
    print("Initialization complete.")