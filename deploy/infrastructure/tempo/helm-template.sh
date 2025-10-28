#!/bin/bash -x

# namespace you use for observability
kubectl create ns observability || true

helm repo add grafana https://grafana.github.io/helm-charts

helm repo update

helm show values grafana/tempo > default-values.yaml

helm template grafana-tempo --namespace observability grafana/tempo -f ./custom-values.yaml > all-resources.yaml
