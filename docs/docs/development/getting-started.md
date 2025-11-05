# Getting Started with Development

## Why Develop Locally?

Working with this platform locally gives you hands-on experience with production-grade development practices:

**Learn by doing** - Instead of just reading about GitOps, observability, and cloud-native patterns, you'll actually work with them. Make changes, see traces flow through Grafana, trigger GitOps deployments, and debug distributed systems.

**Iterate quickly** - Hot reloading with Air for Go services means your changes appear instantly. No waiting for container rebuilds during development. Test MCP integrations, modify API endpoints, and experiment with observability without the CI/CD overhead.

**Understand the full stack** - Run the entire system locally—from AI assistant to database—and see how components interact. Debug trace propagation, test backup procedures, and understand how Kubernetes operators work in a safe environment.

This isn't just running code. It's practicing the skills that matter in production systems.

## Prerequisites

Before you begin, ensure you have the following installed:

- **K3s** - for running the platform in a local Kubernetes cluster
- **kubectl** - for Kubernetes cluster interaction
- **Go 1.21 or higher** - for Go services
- **Python 3.11 or higher** - for Python CLI tools
- **Docker** - for building and testing containers
- **PostgreSQL** - for local database development (optional)
- **Git** - for version control

## Repository Overview

This repository contains:

- **Go Services** (`services/`): REST API services built with Go
  - `todo-api/`: Main todo REST API service
- **Python Tools** (`apps/`): CLI tools built with Python
  - `todops-cli/`: Operations CLI for the todo platform
- **Infrastructure** (`infra/`): Container images for infrastructure components
- **Deployments** (`deploy/`): Kubernetes manifests and GitOps configurations

## Local Kubernetes Setup

Experience the full platform stack with a lightweight K3s cluster running on your machine.

??? note "Installing K3s"
    K3s is a lightweight Kubernetes distribution perfect for local development and testing.

    **Install K3s:**
    ```bash
    curl -sfL https://get.k3s.io | sh -
    ```

    **Verify installation:**
    ```bash
    sudo k3s kubectl get nodes
    ```

    **Set up kubectl access:**
    ```bash
    # Copy k3s kubeconfig to default location
    mkdir -p ~/.kube
    sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
    sudo chown $USER:$USER ~/.kube/config

    # Test kubectl
    kubectl get nodes
    ```

    **Why K3s?**

    - **Lightweight**: Single binary, minimal resource usage (~512MB RAM)
    - **Fast**: Cluster starts in seconds, not minutes
    - **Production-like**: Real Kubernetes, not a simulation
    - **Self-contained**: Everything runs locally, no cloud dependencies

??? note "Deploying the Platform to K3s"
    Once K3s is running, deploy the full stack using the bootstrap script:

    ```bash
    # Navigate to bootstrap directory
    cd deploy/bootstrap

    # Run the bootstrap script
    ./bootstrap.sh
    ```

    This installs:

    - **ArgoCD** - GitOps controller for automated deployments
    - **GitHub Actions Runners (ARC)** - Self-hosted CI/CD runners
    - **CloudNativePG** - PostgreSQL operator for database HA
    - **Observability Stack** - Prometheus, Tempo, Loki, Grafana
    - **MinIO** - S3-compatible storage for backups and logs

    The bootstrap process demonstrates infrastructure-as-code and operator patterns in action.

??? note "Working with Your Local Cluster"
    **Check cluster status:**
    ```bash
    kubectl get pods -A
    kubectl get applications -n argocd
    ```

    **Access services:**
    ```bash
    # Grafana (monitoring)
    kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

    # ArgoCD (deployments)
    kubectl port-forward -n argocd svc/argocd-server 8080:80
    ```

    **Stop K3s:**
    ```bash
    sudo systemctl stop k3s
    ```

    **Uninstall K3s:**
    ```bash
    /usr/local/bin/k3s-uninstall.sh
    ```

## Golang Development Setup

Learn production Go development with dependency management, hot reloading, and environment configuration.

??? note "Initial Setup"
    1. Navigate to the Go service directory:
    ```bash
    cd services/todo-api
    ```

    2. Download and verify dependencies:
    ```bash
    go mod download
    ```

    3. Clean up and verify `go.mod` and `go.sum`:
    ```bash
    go mod tidy
    ```

    This ensures all dependencies are properly resolved and recorded.

??? note "Running the Service Locally"
    Create a `.env` file:
    ```bash
    cp .env.example .env
    # Edit .env with your local configuration
    ```

    **Option 1: Standard Go Run**
    ```bash
    go run main.go
    ```

    The server will start on `http://localhost:8080`.

    **Option 2: Hot Reloading with Air**

    Air provides live reloading during development, automatically rebuilding and restarting when you save changes.

    1. Install Air:
    ```bash
    go install github.com/air-verse/air@latest
    ```

    2. Ensure `$GOPATH/bin` or `$HOME/go/bin` is in your PATH:
    ```bash
    export PATH=$PATH:$(go env GOPATH)/bin
    ```

    3. Initial air configuration:
    ```bash
    cd services/todo-api
    air init
    ```

    4. Run with Air:
    ```bash
    air
    ```

    Air will watch for file changes and automatically rebuild and restart the service.

    **Configuration:**
    Air looks for `.air.toml` in the service directory. The default configuration typically works well, but you can customize:

    - Build commands
    - File watch patterns
    - Excluded directories
    - Delay between rebuilds


## Python Development Setup

Build operational CLI tools with Python virtual environments, editable installs, and environment configuration.

??? note "Setting Up todops-cli"
    The `todops` CLI tool is used for platform operations like searching logs, managing ignore lists, and posting to Slack.

    1. Navigate to the CLI directory:
    ```bash
    cd apps/todops-cli
    ```

    2. Create a virtual environment:
    ```bash
    python3 -m venv venv
    ```

    3. Activate the virtual environment:
    ```bash
    source venv/bin/activate
    ```

    4. Install in editable mode (for development):
    ```bash
    pip install -e .
    ```

    The `-e` flag installs the package in "editable" mode, meaning changes to the source code are immediately reflected without needing to reinstall.

??? note "Development Workflow"
    1. Make changes to Python code in the `apps/todops-cli/` directory
    2. Changes are immediately available (no reinstall needed with `-e` flag)
    3. Test with: `todops --help` or any todops command

    Example workflow:
    ```bash
    # Activate venv
    source venv/bin/activate

    # Make changes to code
    vi todops/loki_commands.py

    # Test immediately
    todops loki search "error" --since "1h"

    # Deactivate when done
    deactivate
    ```

??? note "Environment Variables"
    Create a `.env` file in `apps/todops-cli/` for local development:

    ```bash
    # Loki configuration
    LOKI_URL=http://localhost:3100

    # MinIO configuration (for ignore list storage)
    MINIO_URL=localhost:9000
    MINIO_ACCESS_KEY=your-access-key
    MINIO_SECRET_KEY=your-secret-key

    # Slack configuration (for notifications)
    SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
    ```

    The CLI will automatically load these from `.env` when running locally.

## Docker Development

Practice containerization and image building for local testing before CI/CD pipelines.

??? note "Building Images Locally"
    **Todo API:**
    ```bash
    cd services/todo-api
    docker build -t todo-api:local .
    ```

    **todops-cli (built as part of Dagu):**
    ```bash
    cd infra/dagu
    docker build -t dagu:local .
    ```

## Database Setup

Understand how to run PostgreSQL locally and connect to production CloudNativePG clusters.

??? note "Local PostgreSQL"
    If running services locally, you'll need a PostgreSQL database.

    **Using Docker:**
    ```bash
    docker run --name todo-postgres \
      -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=postgres \
      -e POSTGRES_DB=todo_db \
      -p 5432:5432 \
      -d postgres:15
    ```

    **Connect from your service:**
    ```bash
    export SERVER_PORT=8080
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_USER=postgres
    export DB_PASSWORD=postgres
    export DB_NAME=todo_db
    export DB_SSLMODE=disable
    export OTEL_ENABLE_STDOUT=true
    ```

??? note "Cluster Database"
    In the Kubernetes cluster, services connect to CloudNativePG:

    - **Connection**: `todo-db-rw.cnpg.svc.cluster.local:5432`
    - **Database**: `todo_db`
    - **Credentials**: Stored in `todo-api-secret` Kubernetes secret

## Port Forwarding for Local Development

Access observability tools, databases, and storage from your local machine while they run in the cluster.

??? note "Port Forwarding Commands"
    To access cluster services from your local machine:

    ```bash
    # Loki (Logs)
    kubectl port-forward -n logging svc/loki-gateway 3100:80

    # MinIO (Object Storage)
    kubectl port-forward -n minio svc/minio 9000:9000 9001:9001

    # PostgreSQL (Database)
    kubectl port-forward -n cnpg svc/todo-db-rw 5432:5432

    # Grafana (Dashboards)
    kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
    ```

## What to Explore Next

Now that you have the platform running locally, here's how to get the most value:

**[Understand the System Design →](../architecture/overview.md)**
See how components connect, understand data flows, and learn why architectural decisions were made. This shows how to think about system design, not just implementation.

**[Deploy Like Production →](../deployment/kubernetes.md)**
Experience the full GitOps workflow: make a code change, push to Git, watch ArgoCD sync, verify deployment, see observability data flow. This is how real deployments work.

**[Debug with Observability →](../observability/opentelemetry.md)**
Make an API call and watch the trace flow from MCP → API → Database → Grafana. Practice using distributed tracing to debug issues before they hit production.

**Practice makes permanent** - The more you experiment with this stack locally, the more comfortable you'll be building and operating production systems.