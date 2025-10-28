#!/bin/bash -x

# namespace you use for observability
kubectl create ns observability || true

helm repo add grafana https://grafana.github.io/helm-charts

helm repo update

helm show values grafana/tempo > default-values.yaml

helm template tempo --namespace observability grafana/tempo -f ./custom-values.yaml > all-resources.yaml



# grafana:
#   additionalDataSources:
#     - name: Tempo
#       type: tempo
#       access: proxy
#       url: http://tempo.observability.svc.cluster.local:3100
#       isDefault: false
#       jsonData:
#         nodeGraph:
#           enabled: true
#         tracesToLogs:
#           # If you also have Loki, wire correlation:
#           datasourceUid: loki
#           spanStartTimeShift: '1h'
#           spanEndTimeShift: '1h'
#         tracesToMetrics:
#           datasourceUid: prometheus