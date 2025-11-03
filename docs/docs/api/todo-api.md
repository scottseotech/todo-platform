# Todo API Reference

**Version:** 1.0.0

A simple REST API for managing todos with PostgreSQL backend.

## Base URLs

| Environment | URL |
|-------------|-----|
| Local Development | `http://localhost:8080` |
| Production | `https://todo-api.scottseo.tech` |

## Overview

The Todo API provides a simple CRUD (Create, Read, Update, Delete) interface for managing todo items. All endpoints return JSON responses and use standard HTTP status codes.

## Authentication

Currently, the API does not require authentication. This is intended for demonstration purposes.

## Endpoints

### Health Check

#### GET /health

Returns the health status of the API.

**Tags:** Health

**Responses:**

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | Service is healthy | [HealthResponse](#healthresponse) |

**Example Request:**

```bash
curl http://localhost:8080/health
```

**Example Response:**

```json
{
  "status": "healthy"
}
```

---

### Todos

#### GET /api/v1/todos

Retrieves a list of all todos.

**Tags:** Todos

**Responses:**

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | A list of todos | Array of [Todo](#todo) |
| 500 | Internal server error | [Error](#error) |

**Example Request:**

```bash
curl http://localhost:8080/api/v1/todos
```

**Example Response:**

```json
[
  {
    "id": 1,
    "title": "Buy groceries",
    "due_date": "2024-12-31T23:59:59Z",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  {
    "id": 2,
    "title": "Complete project documentation",
    "due_date": null,
    "created_at": "2024-01-02T14:30:00Z",
    "updated_at": "2024-01-02T14:30:00Z"
  }
]
```

---

#### POST /api/v1/todos

Creates a new todo item.

**Tags:** Todos

**Request Body:**

Content-Type: `application/json`

Schema: [CreateTodoRequest](#createtodorequest)

**Responses:**

| Status | Description | Schema |
|--------|-------------|--------|
| 201 | Todo created successfully | [Todo](#todo) |
| 400 | Invalid request body | [Error](#error) |
| 500 | Internal server error | [Error](#error) |

**Example Request:**

```bash
curl -X POST http://localhost:8080/api/v1/todos \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "due_date": "2024-12-31T23:59:59Z"
  }'
```

**Example Response:**

```json
{
  "id": 1,
  "title": "Buy groceries",
  "due_date": "2024-12-31T23:59:59Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

---

#### GET /api/v1/todos/{id}

Retrieves a specific todo by its ID.

**Tags:** Todos

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | Yes | The ID of the todo to retrieve (minimum: 1) |

**Responses:**

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | Todo found | [Todo](#todo) |
| 400 | Invalid todo ID | [Error](#error) |
| 404 | Todo not found | [Error](#error) |

**Example Request:**

```bash
curl http://localhost:8080/api/v1/todos/1
```

**Example Response:**

```json
{
  "id": 1,
  "title": "Buy groceries",
  "due_date": "2024-12-31T23:59:59Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Error Response (404):**

```json
{
  "error": "Todo not found"
}
```

---

#### PUT /api/v1/todos/{id}

Updates an existing todo item. Only provided fields will be updated.

**Tags:** Todos

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | Yes | The ID of the todo to update (minimum: 1) |

**Request Body:**

Content-Type: `application/json`

Schema: [UpdateTodoRequest](#updatetodorequest)

**Responses:**

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | Todo updated successfully | [Todo](#todo) |
| 400 | Invalid request | [Error](#error) |
| 404 | Todo not found | [Error](#error) |
| 500 | Internal server error | [Error](#error) |

**Example Request:**

```bash
curl -X PUT http://localhost:8080/api/v1/todos/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries and cook dinner"
  }'
```

**Example Response:**

```json
{
  "id": 1,
  "title": "Buy groceries and cook dinner",
  "due_date": "2024-12-31T23:59:59Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T15:30:00Z"
}
```

---

#### DELETE /api/v1/todos/{id}

Deletes a todo by its ID.

**Tags:** Todos

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | Yes | The ID of the todo to delete (minimum: 1) |

**Responses:**

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | Todo deleted successfully | [DeleteResponse](#deleteresponse) |
| 400 | Invalid todo ID | [Error](#error) |
| 404 | Todo not found | [Error](#error) |
| 500 | Internal server error | [Error](#error) |

**Example Request:**

```bash
curl -X DELETE http://localhost:8080/api/v1/todos/1
```

**Example Response:**

```json
{
  "message": "Todo deleted successfully!"
}
```

---

## Schemas

### Todo

Represents a todo item.

**Properties:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| id | integer | Yes | Unique identifier for the todo | `1` |
| title | string | Yes | Title of the todo item | `"Buy groceries"` |
| due_date | string (date-time) | No | Optional due date for the todo (nullable) | `"2024-12-31T23:59:59Z"` |
| created_at | string (date-time) | Yes | Timestamp when the todo was created | `"2024-01-01T10:00:00Z"` |
| updated_at | string (date-time) | Yes | Timestamp when the todo was last updated | `"2024-01-01T10:00:00Z"` |

**Example:**

```json
{
  "id": 1,
  "title": "Buy groceries",
  "due_date": "2024-12-31T23:59:59Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

---

### CreateTodoRequest

Request body for creating a new todo.

**Properties:**

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| title | string | Yes | minLength: 1 | Title of the todo item | `"Buy groceries"` |
| due_date | string (date-time) | No | nullable | Optional due date for the todo | `"2024-12-31T23:59:59Z"` |

**Example:**

```json
{
  "title": "Buy groceries",
  "due_date": "2024-12-31T23:59:59Z"
}
```

---

### UpdateTodoRequest

Request body for updating an existing todo. At least one field must be provided for update.

**Properties:**

| Field | Type | Required | Constraints | Description | Example |
|-------|------|----------|-------------|-------------|---------|
| title | string | No | minLength: 1 | Updated title of the todo item | `"Buy groceries and cook dinner"` |
| due_date | string (date-time) | No | nullable | Updated due date for the todo | `"2024-12-31T23:59:59Z"` |

**Example:**

```json
{
  "title": "Buy groceries and cook dinner",
  "due_date": "2024-12-31T23:59:59Z"
}
```

---

### Error

Standard error response.

**Properties:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| error | string | Yes | Error message | `"Todo not found"` |

**Example:**

```json
{
  "error": "Todo not found"
}
```

---

### HealthResponse

Health check response.

**Properties:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| status | string | No | Health status | `"healthy"` |

**Example:**

```json
{
  "status": "healthy"
}
```

---

### DeleteResponse

Response for successful deletion.

**Properties:**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| message | string | No | Success message | `"Todo deleted successfully!"` |

**Example:**

```json
{
  "message": "Todo deleted successfully!"
}
```

---

## HTTP Status Codes

The API uses standard HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | OK - Request succeeded |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request parameters or body |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error occurred |

## Error Handling

All error responses follow a consistent format using the [Error](#error) schema.

**Common Errors:**

| Status | Error Message | Cause |
|--------|---------------|-------|
| 400 | "Invalid request body" | Malformed JSON or missing required fields |
| 400 | "Invalid todo ID" | Non-numeric or negative ID parameter |
| 404 | "Todo not found" | Todo with specified ID doesn't exist |
| 500 | Various messages | Database connection errors, unexpected server errors |

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions.

## Data Types

### Date-Time Format

All date-time fields use ISO 8601 format with UTC timezone:

```
YYYY-MM-DDTHH:MM:SSZ
```

Example: `2024-12-31T23:59:59Z`

### Nullable Fields

Fields marked as nullable can accept `null` values or be omitted from responses:

- `Todo.due_date`
- `CreateTodoRequest.due_date`
- `UpdateTodoRequest.due_date`

## Client Libraries

Generated client libraries are available:

- **Go**: [clients/todo-client-go/](../../clients/todo-client-go/)
- **Python**: Coming soon
- **TypeScript**: Coming soon

## OpenAPI Specification

The complete OpenAPI 3.0.3 specification is available at:

- **File**: [services/todo-api/openapi.json](../../../services/todo-api/openapi.json)
- **Interactive UI**: Available when running the API locally (future feature)

## Testing the API

### Using curl

All examples in this documentation use `curl`. Ensure you replace `localhost:8080` with your actual API base URL.

### Using Postman

Import the OpenAPI specification into Postman:

1. Open Postman
2. Click Import
3. Select "Link" and paste the URL to `openapi.json`
4. Postman will generate a collection with all endpoints

### Using httpie

```bash
# Get all todos
http GET localhost:8080/api/v1/todos

# Create a todo
http POST localhost:8080/api/v1/todos title="Buy groceries" due_date="2024-12-31T23:59:59Z"

# Get a specific todo
http GET localhost:8080/api/v1/todos/1

# Update a todo
http PUT localhost:8080/api/v1/todos/1 title="Buy groceries and cook dinner"

# Delete a todo
http DELETE localhost:8080/api/v1/todos/1
```

## Changelog

### Version 1.0.0

Initial release with:
- CRUD operations for todos
- Health check endpoint
- PostgreSQL backend
- OpenTelemetry instrumentation
- Prometheus metrics

## Support

For issues or questions:
- GitHub Issues: [todo-platform/issues](https://github.com/scottseotech/todo-platform/issues)
- Documentation: [Getting Started](../development/getting-started.md)
