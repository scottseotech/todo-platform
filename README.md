# Setup

## Initial directory structure
```
  .github/workflows/
    build-api.yml
    release.yml               # bump chart, push image, notify Slack
    chatops.yml               # dispatch from /deploy  
  services/
    todo-api/                 # Go, OTEL, /metrics, Dockerfile
    todo-cli/                 # Go CLI + k6 fixtures
    todo-mcp/                 # Go
    todo-bot/                 # Python /ship, /todo, GitHub dispatch
  clients/
    todo-client-go/           # golang client
  deploy/
    applications/             # k8s applications
    argocd-apps/              # ArgoCD applications
    infrastructure            # k8s backend infrastructure
  k6/
    load.js                   # quick ramp test
  infra/
    homer/                    # homer
    runner/                   # Github ARC runner
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

show artificial drawing of my lab environment

user -> slack slash command -> todo-api -> database

user simulation of 100 users

capture metrics for 