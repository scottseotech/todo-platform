#!/bin/bash -x

APP_NAME=fluent-bit
NAMESPACE=logging

helm repo add grafana https://grafana.github.io/helm-charts

helm repo update

helm show values grafana/fluent-bit > default-values.yaml 

helm template fluent-bit grafana/fluent-bit --namespace $NAMESPACE -f ./custom-values.yaml > all-resources.yaml

kustomize edit set namespace $NAMESPACE

git add .

git commit -m "updating ${APP_NAME}"

git push origin main


# Manual step while setting up loki datasource
#
# In Add Datasource
# HTTP Headers > Add Header > X-Scope-OrgID: todo
# The header is not necessary if we set loki.auth_enabled to false