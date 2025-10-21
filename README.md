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
