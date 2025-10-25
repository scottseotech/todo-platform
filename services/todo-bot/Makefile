.PHONY: install dev run clean docker-build

# Install dependencies including local todo-client
install:
	pip install -e ../../clients/todo-client-python
	pip install -r requirements.txt

# Run in development mode with auto-reload
dev:
	@echo "🔧 Starting in development mode with auto-reload..."
	@watchmedo auto-restart \
		--directory=. \
		--pattern="*.py" \
		--recursive \
		-- python app.py

# Run normally (production mode)
run:
	python app.py

# Build Docker image (must run from repo root)
docker-build:
	@echo "🐳 Building Docker image from repo root..."
	@cd ../.. && docker build -f services/todo-bot/Dockerfile -t todo-bot .

# Clean Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
