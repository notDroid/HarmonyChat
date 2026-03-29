# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import os
import subprocess
import re

def main():
    key_file = "keys.txt"
    sops_file = ".sops.yaml"

    # 1. Generate the keypair if it doesn't exist
    if not os.path.exists(key_file):
        print(f"Generating new age keypair at {key_file}...")
        try:
            subprocess.run(["age-keygen", "-o", key_file], check=True)
        except FileNotFoundError:
            print("❌ Error: 'age-keygen' is not installed or not in your PATH.")
            print("Please install it first (e.g., 'brew install age' or 'apt install age').")
            return
    else:
        print(f"{key_file} already exists. Skipping generation.")

    # 2. Extract the public key
    with open(key_file, "r") as f:
        content = f.read()
    
    # age-keygen outputs the public key as a comment: "# public key: age1..."
    match = re.search(r"# public key: (age1[a-z0-9]+)", content)
    if not match:
        print(f"❌ Error: Could not find a valid age public key in {key_file}")
        return

    pub_key = match.group(1)
    print(f"Configuring {sops_file} with public key: {pub_key}")

    # 3. Write the .sops.yaml file
    sops_config = f"""creation_rules:
  - path_regex: secrets\\.yaml
    encrypted_regex: '^(secrets)$'
    age: '{pub_key}'
"""
    with open(sops_file, "w") as f:
        f.write(sops_config)
    
    print("✅ SOPS configured successfully!")

if __name__ == "__main__":
    main()