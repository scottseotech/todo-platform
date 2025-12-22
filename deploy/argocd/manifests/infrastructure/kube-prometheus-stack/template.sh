#!/bin/bash -x

APP_NAME=prometheus-operator

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm repo update

helm show values prometheus-community/kube-prometheus-stack > default-values.yaml 

helm template kube-prometheus-stack --namespace monitoring prometheus-community/kube-prometheus-stack -f ./custom-values.yaml > all-resources.yaml

git add .

git commit -m "updating ${APP_NAME}"

git push origin main