#!/bin/bash
# Install ArgoCD CRDs only (not the full manifest)
# Uses kustomize to apply only CRDs from the official ArgoCD repository

set -e

echo "Installing ArgoCD CRDs v3.2.3..."

# Install only the CRDs using kustomize
kubectl apply -k "https://github.com/argoproj/argo-cd/manifests/crds?ref=v3.2.3"

echo "✓ ArgoCD CRDs installed successfully"