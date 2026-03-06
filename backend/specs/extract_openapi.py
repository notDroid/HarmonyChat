import json
from harmony.api.main import app

# Prints the OpenAPI schema to stdout, which can be redirected to a file in the Taskfile
def export_openapi(app):    
    openapi_data = app.openapi()
    print(json.dumps(openapi_data, indent=2))

if __name__ == "__main__":
    export_openapi(app)