#!/bin/bash

# GitHub Actions Runner Scale Set Generator
# Uses the reusable helm-template-splitter.sh script

# Do the following first time:
# helm pull oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
# helm show values oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set > default-values.yaml

# Path to the reusable script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELM_SPLITTER="$SCRIPT_DIR/../../bootstrap/helm-template-splitter.sh"

# Check if the reusable script exists
if [[ ! -f "$HELM_SPLITTER" ]]; then
    echo "Error: helm-template-splitter.sh not found at $HELM_SPLITTER"
    echo "Please ensure the script exists in the bootstrap directory"
    exit 1
fi

# Run the reusable script with the specific parameters for GHA runners
exec "$HELM_SPLITTER" \
    --release-name arc-runner-set \
    --namespace arc-runners \
    --chart oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set \
    --values-file ./custom-values.yaml \
    --output-dir output