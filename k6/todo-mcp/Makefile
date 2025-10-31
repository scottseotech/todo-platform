.PHONY: help smoke load local production install clean

help:
	@echo "K6 Load Test Commands for todo-mcp"
	@echo "===================================="
	@echo "make smoke        - Run smoke test (1 user, 30s)"
	@echo "make load         - Run full load test (ramping load)"
	@echo "make local        - Run smoke test against localhost"
	@echo "make production   - Run load test against production"
	@echo "make install      - Install k6 (macOS only)"
	@echo "make clean        - Clean up test results"

# Quick smoke test
smoke:
	@echo "Running smoke test..."
	k6 run --vus 1 --duration 30s todo-mcp-load-test.js

# Full load test
load:
	@echo "Running load test..."
	k6 run todo-mcp-load-test.js

# Test against local development
local:
	@echo "Testing against localhost:8081..."
	k6 run --env TODO_MCP_URL=http://localhost:8081 --vus 1 --duration 30s todo-mcp-load-test.js

# Test against production (use with caution!)
production:
	@echo "⚠️  Testing against production..."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		k6 run --env TODO_MCP_URL=https://todo-mcp.scottseo.tech todo-mcp-load-test.js; \
	fi

# Custom runs with parameters
quick:
	@echo "Quick test: 5 users for 1 minute..."
	k6 run --vus 5 --duration 1m todo-mcp-load-test.js

stress:
	@echo "Stress test: 200 users for 2 minutes..."
	k6 run --vus 200 --duration 2m todo-mcp-load-test.js

spike:
	@echo "Spike test: 500 users for 30 seconds..."
	k6 run --vus 500 --duration 30s todo-mcp-load-test.js

# Install k6 (macOS)
install:
	@echo "Installing k6..."
	@if command -v brew >/dev/null 2>&1; then \
		brew install k6; \
	else \
		echo "Homebrew not found. Install from: https://k6.io/docs/getting-started/installation/"; \
	fi

# Clean up
clean:
	@echo "Cleaning up test results..."
	rm -f *.json *.csv results.txt
