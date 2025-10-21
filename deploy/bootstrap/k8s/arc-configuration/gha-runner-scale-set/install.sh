#!/bin/bash

helm install arc-runner-set     \
    --namespace arc-runners     \
    --create-namespace          \
    -f custom-values.yaml       \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set

kubectl apply -f ./github-runner-role.yaml