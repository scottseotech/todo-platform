import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Custom metrics
const todoCreated = new Counter('todo_created');
const todoListed = new Counter('todo_listed');
const todoUpdated = new Counter('todo_updated');
const todoDeleted = new Counter('todo_deleted');
const toolCallDuration = new Trend('tool_call_duration');

// Load test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users over 30s
    { duration: '1m', target: 10 },   // Stay at 10 users for 1m
    { duration: '30s', target: 50 },  // Ramp up to 50 users over 30s
    { duration: '2m', target: 50 },   // Stay at 50 users for 2m
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% of requests should fail
  },
};

// Base URL for todo-mcp service
const BASE_URL = __ENV.TODO_MCP_URL || 'http://localhost:8081';

// Helper function to call MCP tool via HTTP endpoint
function callTool(toolName, input) {
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: '10s',
  };

  const startTime = Date.now();
  const response = http.post(
    `${BASE_URL}/tools/${toolName}/invoke`,
    JSON.stringify(input),
    params
  );
  const duration = Date.now() - startTime;

  toolCallDuration.add(duration);

  return response;
}

// Test scenario: Create a todo
export function testCreateTodo() {
  const title = `Load test todo ${Date.now()}-${__VU}`;
  const response = callTool('todos-add', {
    title: title,
    due_date: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
  });

  const success = check(response, {
    'create: status is 200': (r) => r.status === 200,
    'create: has response body': (r) => r.body && r.body.length > 0,
  });

  if (success) {
    todoCreated.add(1);
  }

  return response;
}

// Test scenario: List todos
export function testListTodos() {
  const response = callTool('todos-list', {});

  const success = check(response, {
    'list: status is 200': (r) => r.status === 200,
    'list: has response body': (r) => r.body && r.body.length > 0,
  });

  if (success) {
    todoListed.add(1);
  }

  return response;
}

// Test scenario: Update a todo
export function testUpdateTodo(todoId) {
  const response = callTool('todos-update', {
    id: todoId,
    title: `Updated todo ${Date.now()}`,
  });

  const success = check(response, {
    'update: status is 200': (r) => r.status === 200,
  });

  if (success) {
    todoUpdated.add(1);
  }

  return response;
}

// Test scenario: Delete a todo
export function testDeleteTodo(todoId) {
  const response = callTool('todos-delete', {
    id: todoId,
  });

  const success = check(response, {
    'delete: status is 200': (r) => r.status === 200,
  });

  if (success) {
    todoDeleted.add(1);
  }

  return response;
}

// Main test execution
export default function () {
  // Test flow: Create -> List -> Update -> Delete

  // 1. Create a todo
  const createResponse = testCreateTodo();

  // Small delay between operations
  sleep(0.1);

  // 2. List todos
  testListTodos();

  sleep(0.1);

  // 3. Parse created todo ID from response (if successful)
  if (createResponse.status === 200) {
    try {
      const body = JSON.parse(createResponse.body);

      // MCP JSON-RPC response format
      if (body.result) {
        // Try to extract ID from response text
        // This depends on your actual response format
        // Adjust based on actual MCP response structure

        // For now, use a static ID for testing
        // In production, you'd parse the actual ID from the create response
        const todoId = 1; // Placeholder - adjust based on actual response

        sleep(0.1);

        // 4. Update the todo
        testUpdateTodo(todoId);

        sleep(0.1);

        // 5. Delete the todo
        testDeleteTodo(todoId);
      }
    } catch (e) {
      console.error('Failed to parse response:', e);
    }
  }

  // Random sleep between iterations (1-3 seconds)
  sleep(Math.random() * 2 + 1);
}

// Smoke test scenario - quick validation
export function smokeTest() {
  const response = callTool('todos-list', {});

  check(response, {
    'smoke: service is up': (r) => r.status === 200,
    'smoke: response time < 1s': (r) => r.timings.duration < 1000,
  });
}

// Setup function - runs once before the test
export function setup() {
  console.log(`Starting load test against ${BASE_URL}`);

  // Verify service is healthy
  const healthResponse = http.get(`${BASE_URL}/health`);
  if (healthResponse.status !== 200) {
    throw new Error('Service health check failed');
  }

  console.log('Service is healthy, proceeding with load test');
}

// Teardown function - runs once after the test
export function teardown(data) {
  console.log('Load test completed');
}
