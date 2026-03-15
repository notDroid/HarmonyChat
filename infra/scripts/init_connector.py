'''
Initialize kafka connector
'''
import urllib.request
import urllib.error

def register_connector(connect_url, config_file):
    print(f"Registering Connector from {config_file}...")
    with open(config_file, 'r') as f:
        config_data = f.read().encode('utf-8')
    
    req = urllib.request.Request(
        connect_url, 
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