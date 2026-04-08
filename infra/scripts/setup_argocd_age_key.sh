#!/bin/bash
# Extracts the SOPS Age private key and creates a Kubernetes secret in the argocd namespace

NAMESPACE="argocd"
SECRET_NAME="sops-age-key"
KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"

if [ ! -f "$KEY_FILE" ]; then
    echo "Error: Age key file not found at $KEY_FILE"
    echo "Please set SOPS_AGE_KEY_FILE environment variable if it's located elsewhere."
    exit 1
fi

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic "$SECRET_NAME" \
    --namespace "$NAMESPACE" \
    --from-file=keys.txt="$KEY_FILE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "Successfully created secret $SECRET_NAME in namespace $NAMESPACE"