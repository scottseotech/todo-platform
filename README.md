# Setup

## Initial directory structure
```
  services/
    todo-api/         # Go, OTEL, /metrics, Dockerfile
    todo-cli/         # Go CLI + k6 fixtures
    slackbot/         # /deploy, /todo, GitHub dispatch
    mcp-todo/         # optional
  deploy/
    charts/           # Helm chart w/ Rollouts
    kustomize/        # overlays: dev/stage/prod
  k6/
    load.js           # quick ramp test
  .github/workflows/
    build-api.yml
    release.yml       # bump chart, push image, notify Slack
    chatops.yml       # dispatch from /deploy
  infra/
    loki/ prom/ grafana/  # values or manifests
    cnpg/                 # cluster + backup CRs
```

execute `bootstrap.sh`

k create ns cnpg

### ArgoCD
ArgoCD changes must be applied using patches in k8s/argocd folder

argocd account generate-token --account admin

### CNPG 
psql -h 192.168.

```
CREATE SCHEMA todo;

ALTER USER todo_db_admin SET search_path TO todo;
```

four github secrets
ARGOCD_TOKEN
DOCKERHUB_TOKEN
DOCKERHUB_USERNAME
GH_ACCESS_TOKEN

todo-platform variable
ARGOCD_LOCK