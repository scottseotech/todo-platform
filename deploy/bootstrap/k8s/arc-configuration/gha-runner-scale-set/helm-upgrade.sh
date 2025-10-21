#!/bin/bash -xe

# upgrade.sh will push the new version. we got to pull first in order to use the new version.
git pull

helm upgrade arc-runner-set \
    -f custom-values.yaml                                                           \
    --namespace arc-runners                                                         \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set