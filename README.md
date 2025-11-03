# About
So this repository came about to showcase my devops, chatops, and mlops skills using a simple todo list app.

# About This Lab
I built this lab to experiment with K8s, GitHub Actions, and observability pipelines in a realistic setup

![image](https://github.com/scottseotech/todo-platform/blob/main/assets/images/homelab.jpg?raw=true)


## Initial directory structure
```
  .github/workflows/          # push image, notify Slack
  apps/todops-cli             # Python CLI
  services/
    todo-api/                 # Go, OTEL, /metrics, Dockerfile
    todo-mcp/                 # Go MCP server
    todo-bot/                 # Python Slack bot /ship, /todo
  clients/
    todo-client-go/           # Go todo-api client
  deploy/
    applications/             # k8s applications
    argocd-apps/              # ArgoCD applications
    bootstrap/bootstrap.sh    # Automation script for setting up my homelab
    infrastructure/           # k8s backend infrastructure
  k6/
    load.js                   # quick ramp test
  infra/
    homer/                    # homer
    runner/                   # Github ARC runner
```
