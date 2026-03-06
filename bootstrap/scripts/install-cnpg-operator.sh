#!/bin/bash

echo "Installing CloudNativePG Operator..."

kubectl apply --server-side -f \
    https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.27/releases/cnpg-1.27.0.yaml

echo "Waiting for CloudNativePG controller to be ready..."

kubectl rollout status deployment \
    -n cnpg-system cnpg-controller-manager

echo "✓ CloudNativePG Operator deployment completed!"