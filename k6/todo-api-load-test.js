import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users over 30s
    { duration: '1m', target: 10 },   // Stay at 10 users for 1m
    { duration: '30s', target: 50 },  // Ramp up to 50 users over 30s
    { duration: '2m', target: 50 },   // Stay at 50 users for 2m
    { duration: '30s', target: 100 }, // Spike to 100 users over 30s
    { duration: '1m', target: 100 },  // Stay at 100 users for 1m
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.05'],   // Error rate should be less than 5%
    errors: ['rate<0.05'],            // Custom error metric should be less than 5%
  },
};

// Configuration - can be overridden via environment variables
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API_PREFIX = '/api/v1';

// Helper function to generate random todo title
function randomTitle() {
  const tasks = [
    'Buy groceries',
    'Complete project report',
    'Schedule dentist appointment',
    'Review pull requests',
    'Update documentation',
    'Plan team meeting',
    'Deploy to production',
    'Write unit tests',
    'Fix critical bug',
    'Refactor authentication module'
  ];
  return tasks[Math.floor(Math.random() * tasks.length)] + ` #${Date.now()}`;
}

// Helper function to generate random due date in the future
function randomDueDate() {
  const days = Math.floor(Math.random() * 30) + 1; // 1-30 days from now
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + days);
  return dueDate.toISOString();
}

// Main test scenario - performs complete CRUD lifecycle
export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // 1. Health Check (warm-up)
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health check status is 200': (r) => r.status === 200,
    'health check returns healthy': (r) => JSON.parse(r.body).status === 'healthy',
  }) || errorRate.add(1);

  sleep(0.5);

  // 2. CREATE a new todo
  const createPayload = JSON.stringify({
    title: randomTitle(),
    due_date: randomDueDate(),
  });

  const createRes = http.post(`${BASE_URL}${API_PREFIX}/todos`, createPayload, params);
  const createSuccess = check(createRes, {
    'create todo status is 201': (r) => r.status === 201,
    'create todo returns id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.id !== undefined && body.id > 0;
      } catch (e) {
        return false;
      }
    },
    'create todo returns title': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.title !== undefined && body.title.length > 0;
      } catch (e) {
        return false;
      }
    },
  });

  if (!createSuccess) {
    errorRate.add(1);
    return; // Skip rest of the test if create failed
  }

  const createdTodo = JSON.parse(createRes.body);
  const todoId = createdTodo.id;

  sleep(1);

  // 3. READ the created todo by ID
  const getRes = http.get(`${BASE_URL}${API_PREFIX}/todos/${todoId}`);
  check(getRes, {
    'get todo status is 200': (r) => r.status === 200,
    'get todo returns correct id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.id === todoId;
      } catch (e) {
        return false;
      }
    },
    'get todo has timestamps': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.created_at !== undefined && body.updated_at !== undefined;
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  sleep(1);

  // 4. LIST all todos
  const listRes = http.get(`${BASE_URL}${API_PREFIX}/todos`);
  check(listRes, {
    'list todos status is 200': (r) => r.status === 200,
    'list todos returns array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body);
      } catch (e) {
        return false;
      }
    },
    'list todos includes our todo': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.some(todo => todo.id === todoId);
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  sleep(1);

  // 5. UPDATE the todo
  const updatePayload = JSON.stringify({
    title: `${createdTodo.title} (updated)`,
    due_date: randomDueDate(),
  });

  const updateRes = http.put(`${BASE_URL}${API_PREFIX}/todos/${todoId}`, updatePayload, params);
  check(updateRes, {
    'update todo status is 200': (r) => r.status === 200,
    'update todo returns updated title': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.title.includes('(updated)');
      } catch (e) {
        return false;
      }
    },
    'update todo changed updated_at': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.updated_at !== createdTodo.updated_at;
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  sleep(1);

  // 6. DELETE the todo
  const deleteRes = http.del(`${BASE_URL}${API_PREFIX}/todos/${todoId}`);
  check(deleteRes, {
    'delete todo status is 200': (r) => r.status === 200,
    'delete todo returns success message': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.message !== undefined && body.message.includes('success');
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  sleep(1);

  // 7. Verify DELETE - try to get the deleted todo (should return 404)
  const verifyDeleteRes = http.get(`${BASE_URL}${API_PREFIX}/todos/${todoId}`);
  check(verifyDeleteRes, {
    'verify delete returns 404': (r) => r.status === 404,
  }) || errorRate.add(1);

  // Random sleep between 1-3 seconds before next iteration
  sleep(Math.random() * 2 + 1);
}
