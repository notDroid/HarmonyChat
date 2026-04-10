# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import argparse
import secrets
import string
import getpass
import json
import os
import subprocess
from pathlib import Path

def generate_password(length=24):
    """Generates a secure alphanumeric password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_hex(length=32):
    """Generates a secure hex string."""
    return secrets.token_hex(length)

def get_aws_defaults():
    try:
        aws_access = subprocess.check_output(['aws', 'configure', 'get', 'aws_access_key_id']).decode().strip()
        aws_secret = subprocess.check_output(['aws', 'configure', 'get', 'aws_secret_access_key']).decode().strip()
        return aws_access, aws_secret
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None

def get_spacelift_defaults():
    config_path = Path.home() / '.spacelift' / 'config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                current = data.get("currentProfileAlias")
                if current and current in data.get("profiles", {}):
                    creds = data["profiles"][current].get("credentials", {})
                    return creds.get("endpoint"), creds.get("key_id"), creds.get("key_secret")
        except Exception:
            pass
    return None, None, None

def main():
    parser = argparse.ArgumentParser(description="Generate a secure secrets.yaml file.")
    parser.add_argument("output_file", type=str, help="Path to write the secrets.yaml file")
    parser.add_argument("--env", type=str, default="local", help="The target environment (e.g., local, staging)")
    args = parser.parse_args()

    is_local = args.env.lower() == "local"
    print(f"Generating secrets for environment: {args.env}")

    if is_local:
        aws_access = "test1234"
        aws_secret = "test1234"
        s3_access = "minioadmin"
        s3_secret = "minioadmin"
        spacelift_endpoint = "https://localhost"
        spacelift_key_id = "dummy_id"
        spacelift_key_secret = "dummy_secret"
    else:
        print(f"\n☁️  Please enter credentials for {args.env}:")
        aws_def_access, aws_def_secret = get_aws_defaults()
        if aws_def_access and aws_def_secret:
            use_aws = input("Found existing AWS CLI credentials. Use them? (y/n) [y]: ").strip().lower()
            if use_aws != 'n':
                aws_access, aws_secret = aws_def_access, aws_def_secret
            else:
                aws_access = input("AWS Access Key ID: ").strip()
                aws_secret = getpass.getpass("AWS Secret Access Key: ").strip()
        else:
            aws_access = input("AWS Access Key ID: ").strip()
            aws_secret = getpass.getpass("AWS Secret Access Key: ").strip()
        
        use_same = input("Use the same credentials for S3? (y/n) [y]: ").strip().lower()
        if use_same != 'n':
            s3_access = aws_access
            s3_secret = aws_secret
        else:
            s3_access = input("S3 Access Key: ").strip()
            s3_secret = getpass.getpass("S3 Secret Key: ").strip()
            
        print(f"\n🚀 Please enter Spacelift credentials for {args.env} (Press Enter to skip if not applicable):")
        sl_def_end, sl_def_id, sl_def_sec = get_spacelift_defaults()
        if sl_def_end and sl_def_id and sl_def_sec:
            use_sl = input("Found existing Spacelift CLI profile. Use it? (y/n) [y]: ").strip().lower()
            if use_sl != 'n':
                spacelift_endpoint, spacelift_key_id, spacelift_key_secret = sl_def_end, sl_def_id, sl_def_sec
            else:
                spacelift_endpoint = input("Spacelift API Endpoint (e.g. https://harmony-chat.app.us.spacelift.io): ").strip()
                spacelift_key_id = input("Spacelift API Key ID: ").strip()
                spacelift_key_secret = getpass.getpass("Spacelift API Key Secret: ").strip()
        else:
            spacelift_endpoint = input("Spacelift API Endpoint (e.g. https://harmony-chat.app.us.spacelift.io): ").strip()
            spacelift_key_id = input("Spacelift API Key ID: ").strip()
            spacelift_key_secret = getpass.getpass("Spacelift API Key Secret: ").strip()

    yaml_content = f"""secrets: 
  app:
    secret_key: {generate_hex(32)}
  postgres:
    password: {generate_password(24)}
  aws:
    access_key_id: {aws_access}
    secret_access_key: {aws_secret}
  s3:
    access_key: {s3_access}
    secret_key: {s3_secret}
  centrifugo:
    api_key: {generate_hex(16)}
    admin_password: {generate_password(16)}
    admin_secret: {generate_hex(16)}
  spacelift:
    api_key_endpoint: {spacelift_endpoint or '""'}
    api_key_id: {spacelift_key_id or '""'}
    api_key_secret: {spacelift_key_secret or '""'}
"""

    out_path = Path(args.output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w") as f:
        f.write(yaml_content)
    
    print(f"\n✅ Generated new secure secrets at: {out_path}")

if __name__ == "__main__":
    main()