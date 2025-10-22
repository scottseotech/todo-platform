# Todo API Service

A simple REST API for managing todos built with Go, Gin, and PostgreSQL.

## Features

- RESTful API endpoints for CRUD operations
- PostgreSQL database with GORM
- Numerical ID for todos
- Optional due date field
- Auto-migration support
- Containerized with Docker

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/todos` | Get all todos |
| GET | `/api/v1/todos/:id` | Get a specific todo |
| POST | `/api/v1/todos` | Create a new todo |
| PUT | `/api/v1/todos/:id` | Update a todo |
| DELETE | `/api/v1/todos/:id` | Delete a todo |

## Todo Model

```json
{
  "id": 1,
  "title": "Sample Todo",
  "due_date": "2024-12-31T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Getting Started

### Prerequisites

- Go 1.21 or higher
- PostgreSQL database

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Running Locally

1. Install dependencies:
```bash
go mod download
```

2. Run the application:
```bash
go run main.go
```

The server will start on `http://localhost:8080`

### Running with Docker

1. Build the image:
```bash
docker build -t todo-api .
```

2. Run the container:
```bash
docker run -p 8080:8080 \
  -e DB_HOST=your-db-host \
  -e DB_PORT=5432 \
  -e DB_USER=postgres \
  -e DB_PASSWORD=postgres \
  -e DB_NAME=todo \
  todo-api
```

## Example Usage

### Create a todo:
```bash
curl -X POST http://localhost:8080/api/v1/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "due_date": "2024-12-31T00:00:00Z"}'
```

### Get all todos:
```bash
curl http://localhost:8080/api/v1/todos
```

### Get a specific todo:
```bash
curl http://localhost:8080/api/v1/todos/1
```

### Update a todo:
```bash
curl -X PUT http://localhost:8080/api/v1/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries and cook dinner"}'
```

### Delete a todo:
```bash
curl -X DELETE http://localhost:8080/api/v1/todos/1
```

## Project Structure

```
todo-api/
├── config/          # Configuration management
├── database/        # Database connection and migration
├── handlers/        # HTTP request handlers
├── models/          # Data models
├── main.go          # Application entry point
├── Dockerfile       # Docker configuration
└── README.md        # This file
```
