from init_connectors import register_connectors
from init_dynamodb_tables import init_db

if __name__ == "__main__":
    init_db()    
    register_connectors()
    print("Initialization complete.")