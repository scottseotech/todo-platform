# K6 Load Tests for Todo API

This directory contains K6 load testing scripts for the todo-api service.

## Prerequisites

Install K6:

```bash
# macOS
brew install k6

# Linux (Debian/Ubuntu)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Docker
docker pull grafana/k6
```

## Test Files

### `todo-api-load-test.js`

Main load test that performs complete CRUD operations:
1. Health check
2. Create todo
3. Read todo by ID
4. List all todos
5. Update todo
6. Delete todo
7. Verify deletion

**Load profile:**
- Ramp up to 10 users (30s)
- Stay at 10 users (1m)
- Ramp up to 50 users (30s)
- Stay at 50 users (2m)
- Spike to 100 users (30s)
- Stay at 100 users (1m)
- Ramp down to 0 (30s)

**Performance thresholds:**
- 95th percentile response time < 500ms
- Error rate < 5%

## Running Tests

### Local Development

Run against local todo-api (default: `http://localhost:8080`):

```bash
cd k6
k6 run todo-api-load-test.js
```

### Against Kubernetes Service

Run against todo-api in Kubernetes cluster:

```bash
# Port forward the service
kubectl port-forward -n default svc/todo-api 8080:8080 &

# Run the test
k6 run todo-api-load-test.js

# Or specify the URL explicitly
k6 run --env BASE_URL=http://localhost:8080 todo-api-load-test.js
```

### Against Production

Run against production endpoint:

```bash
k6 run --env BASE_URL=https://todo-api.scottseo.tech todo-api-load-test.js
```

### Quick Smoke Test

Run a quick smoke test with 1 user for 30 seconds:

```bash
k6 run --vus 1 --duration 30s todo-api-load-test.js
```

### Custom Load Profile

Override the test configuration:

```bash
# Constant load: 50 users for 5 minutes
k6 run --vus 50 --duration 5m todo-api-load-test.js

# Stress test: 200 users for 2 minutes
k6 run --vus 200 --duration 2m todo-api-load-test.js
```

## Using Docker

Run K6 tests in Docker:

```bash
# Basic run
docker run --rm -i grafana/k6 run - <todo-api-load-test.js

# With custom BASE_URL (use host.docker.internal on macOS/Windows)
docker run --rm -i -e BASE_URL=http://host.docker.internal:8080 grafana/k6 run - <todo-api-load-test.js

# Mount directory and run
docker run --rm -v $(pwd):/tests grafana/k6 run /tests/todo-api-load-test.js
```

## Interpreting Results

K6 provides comprehensive metrics after each test run:

### Key Metrics

- **http_req_duration**: Response time for HTTP requests
  - `avg`: Average response time
  - `p(95)`: 95th percentile (95% of requests were faster than this)
  - `p(99)`: 99th percentile
- **http_req_failed**: Percentage of failed requests
- **http_reqs**: Total number of HTTP requests
- **vus**: Number of virtual users
- **vus_max**: Maximum number of virtual users reached
- **iterations**: Number of test iterations completed

### Example Output

```
     ✓ health check status is 200
     ✓ create todo status is 201
     ✓ create todo returns id
     ✓ get todo status is 200
     ✓ list todos returns array
     ✓ update todo status is 200
     ✓ delete todo status is 200
     ✓ verify delete returns 404

     checks.........................: 100.00% ✓ 8000      ✗ 0
     data_received..................: 2.1 MB  35 kB/s
     data_sent......................: 1.4 MB  23 kB/s
     errors.........................: 0.00%   ✓ 0         ✗ 1000
     http_req_blocked...............: avg=12.45µs  min=1.2µs   med=4.1µs   max=2.1ms   p(95)=8.2µs   p(99)=15.3µs
     http_req_duration..............: avg=45.23ms  min=3.1ms   med=38.2ms  max=521ms   p(95)=142ms   p(99)=284ms
     http_req_failed................: 0.00%   ✓ 0         ✗ 7000
     http_req_receiving.............: avg=123.4µs  min=12.1µs  med=98.2µs  max=1.2ms   p(95)=245µs   p(99)=412µs
     http_req_sending...............: avg=45.23µs  min=4.5µs   med=32.1µs  max=412µs   p(95)=89.2µs  p(99)=156µs
     http_req_tls_handshaking.......: avg=0s       min=0s      med=0s      max=0s      p(95)=0s      p(99)=0s
     http_req_waiting...............: avg=44.98ms  min=2.9ms   med=37.8ms  max=520ms   p(95)=141ms   p(99)=283ms
     http_reqs......................: 7000    116.666667/s
     iteration_duration.............: avg=8.54s    min=7.5s    med=8.2s    max=10.2s   p(95)=9.8s    p(99)=10.1s
     iterations.....................: 1000    16.666667/s
     vus............................: 100     min=0       max=100
     vus_max........................: 100     min=100     max=100
```

### Threshold Violations

If thresholds are violated, K6 will exit with code 1 and show:

```
✗ http_req_duration..............: p(95)=650ms (threshold violated: p(95)<500)
✗ http_req_failed................: 7.2% (threshold violated: rate<0.05)
```

## Advanced Usage

### Output Results to File

Export results in various formats:

```bash
# JSON output
k6 run --out json=results.json todo-api-load-test.js

# CSV output
k6 run --out csv=results.csv todo-api-load-test.js

# InfluxDB (for Grafana visualization)
k6 run --out influxdb=http://localhost:8086/k6 todo-api-load-test.js
```

### Cloud Results

Upload results to K6 Cloud:

```bash
# Sign up for K6 Cloud and get token
k6 login cloud --token YOUR_TOKEN

# Run and stream results to cloud
k6 run --out cloud todo-api-load-test.js
```

### Environment Variables

The test accepts the following environment variables:

- `BASE_URL`: Base URL of the todo-api (default: `http://localhost:8080`)

Example:

```bash
k6 run --env BASE_URL=https://todo-api.scottseo.tech todo-api-load-test.js
```

## Troubleshooting

### Connection Refused

If you see "connection refused" errors:
1. Verify todo-api is running: `curl http://localhost:8080/health`
2. Check the BASE_URL environment variable
3. For Kubernetes, ensure port-forward is active

### High Error Rate

If error rate exceeds thresholds:
1. Check todo-api logs for errors
2. Verify database connection is stable
3. Check database connection pool size
4. Monitor system resources (CPU, memory, connections)

### Slow Response Times

If p(95) exceeds 500ms:
1. Check database query performance
2. Add database indexes if needed
3. Monitor database connection pool exhaustion
4. Check for N+1 query issues
5. Consider caching frequently accessed data

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Test

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v3

      - name: Install K6
        run: |
          curl https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz -L | tar xvz
          sudo mv k6-v0.47.0-linux-amd64/k6 /usr/local/bin/

      - name: Port forward todo-api
        run: |
          kubectl port-forward -n default svc/todo-api 8080:8080 &
          sleep 5

      - name: Run load test
        run: |
          k6 run k6/todo-api-load-test.js

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: k6-results
          path: results/
```

## Performance Benchmarks

Expected performance for todo-api (based on test environment):

| Metric | Target | Good | Needs Improvement |
|--------|--------|------|-------------------|
| p(95) response time | < 500ms | < 200ms | > 500ms |
| p(99) response time | < 1000ms | < 500ms | > 1000ms |
| Error rate | < 5% | < 1% | > 5% |
| Throughput (req/s) | > 100 | > 500 | < 100 |
| Database connections | < 50 | < 20 | > 50 |

## References

- [K6 Documentation](https://k6.io/docs/)
- [K6 HTTP API](https://k6.io/docs/javascript-api/k6-http/)
- [K6 Checks](https://k6.io/docs/using-k6/checks/)
- [K6 Thresholds](https://k6.io/docs/using-k6/thresholds/)
