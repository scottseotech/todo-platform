# Getting Started with Development

This guide will help you set up your local development environment for the todo platform.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Go 1.21 or higher** - for Go services
- **Python 3.11 or higher** - for Python CLI tools
- **Docker** - for building and testing containers
- **PostgreSQL** - for local database development (optional)
- **kubectl** - for Kubernetes cluster interaction
- **Git** - for version control

## Repository Overview

This repository contains:

- **Go Services** (`services/`): REST API services built with Go
  - `todo-api/`: Main todo REST API service
- **Python Tools** (`apps/`): CLI tools built with Python
  - `todops-cli/`: Operations CLI for the todo platform
- **Infrastructure** (`infra/`): Container images for infrastructure components
- **Deployments** (`deploy/`): Kubernetes manifests and GitOps configurations

## Golang Development Setup

### Initial Setup

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

### Running the Service Locally

Create a `.env` file:
```bash
cp .env.example .env
# Edit .env with your local configuration
```

#### Option 1: Standard Go Run
```bash
go run main.go
```

The server will start on `http://localhost:8080`.

#### Option 2: Hot Reloading with Air

Air provides live reloading during development, automatically rebuilding and restarting when you save changes.

1. Install Air:
```bash
go install github.com/air-verse/air@latest
```

2. Ensure `$GOPATH/bin` or `$HOME/go/bin` is in your PATH:
```bash
export PATH=$PATH:$(go env GOPATH)/bin
```
3. Initial air configuration
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

### Setting Up todops-cli

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

On macOS/Linux:
```bash
source venv/bin/activate
```

4. Install in editable mode (for development):
```bash
pip install -e .
```

The `-e` flag installs the package in "editable" mode, meaning changes to the source code are immediately reflected without needing to reinstall.

### Development Workflow

1. Make changes to Python code in the `apps/todops/` directory
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

### Environment Variables

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

### Building Images Locally

Todo API:
```bash
cd services/todo-api
docker build -t todo-api:local .
```

todops-cli (built as part of Dagu):
```bash
cd infra/dagu
docker build -t dagu:local .
```

## Database Setup

### Local PostgreSQL

If running services locally, you'll need a PostgreSQL database.

Using Docker:
```bash
docker run --name todo-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=todo_db \
  -p 5432:5432 \
  -d postgres:15
```

Connect from your service:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_NAME=todo_db
export DB_SSLMODE=disable
```

### Cluster Database

In the Kubernetes cluster, services connect to CloudNativePG:
- **Connection**: `todo-db-rw.cnpg.svc.cluster.local:5432`
- **Database**: `todo_db`
- **Credentials**: Stored in `todo-api-secret` Kubernetes secret

## Port Forwarding for Local Development

To access cluster services from your local machine:

```bash
# Loki
kubectl port-forward -n logging svc/loki-gateway 3100:80

# MinIO
kubectl port-forward -n minio svc/minio 9000:9000 9001:9001

# PostgreSQL
kubectl port-forward -n cnpg svc/todo-db-rw 5432:5432

# Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

## Next Steps

- Review the [Architecture Overview](../architecture/overview.md)
- Learn about [Kubernetes Deployment](../deployment/kubernetes.md)
- Explore [API Documentation](../api/todo-api.md)