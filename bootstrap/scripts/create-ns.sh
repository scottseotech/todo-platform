#!/bin/bash

kubectl get ns argocd || kubectl create ns argocd

kubectl get ns tools || kubectl create ns tools

kubectl get ns cnpg || kubectl create ns cnpg

kubectl get ns minio || kubectl create ns minio

kubectl get ns observability || kubectl create ns observability

kubectl get ns monitoring || kubectl create ns monitoring

kubectl get ns arc-systems || kubectl create ns arc-systems

kubectl get ns arc-runners || kubectl create ns arc-runners

kubectl get ns signalstack || kubectl create ns signalstack

kubectl get ns todo || kubectl create ns todo