import http from 'k6/http';
import { check, sleep } from 'k6';

// Smoke test configuration - minimal load to verify functionality
export const options = {
  vus: 1,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<1000'], // More lenient for smoke test
    http_req_failed: ['rate<0.01'],    // Very low error tolerance
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API_PREFIX = '/api/v1';

export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Health check
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health check is 200': (r) => r.status === 200,
  });

  sleep(1);

  // Create a todo
  const createRes = http.post(
    `${BASE_URL}${API_PREFIX}/todos`,
    JSON.stringify({
      title: `Smoke test todo ${Date.now()}`,
      due_date: new Date(Date.now() + 86400000).toISOString(), // Tomorrow
    }),
    params
  );

  const createSuccess = check(createRes, {
    'create is 201': (r) => r.status === 201,
  });

  if (!createSuccess) {
    return;
  }

  const todo = JSON.parse(createRes.body);
  sleep(1);

  // Read the todo
  const getRes = http.get(`${BASE_URL}${API_PREFIX}/todos/${todo.id}`);
  check(getRes, {
    'get is 200': (r) => r.status === 200,
  });

  sleep(1);

  // Update the todo
  const updateRes = http.put(
    `${BASE_URL}${API_PREFIX}/todos/${todo.id}`,
    JSON.stringify({
      title: `${todo.title} (updated)`,
    }),
    params
  );
  check(updateRes, {
    'update is 200': (r) => r.status === 200,
  });

  sleep(1);

  // Delete the todo
  const deleteRes = http.del(`${BASE_URL}${API_PREFIX}/todos/${todo.id}`);
  check(deleteRes, {
    'delete is 200': (r) => r.status === 200,
  });

  sleep(1);
}
