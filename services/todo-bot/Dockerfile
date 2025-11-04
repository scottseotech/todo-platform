FROM python:3.11-slim

WORKDIR /app

# Copy todo-client-python first for better layer caching
COPY clients/todo-client-python /tmp/todo-client-python
COPY clients/todo-client-mcp-python /tmp/todo-client-mcp-python

# Install todo-client
RUN pip install --no-cache-dir /tmp/todo-client-python && rm -rf /tmp/todo-client-python
RUN pip install --no-cache-dir /tmp/todo-client-mcp-python && rm -rf /tmp/todo-client-mcp-python

# Copy requirements and install dependencies
COPY services/todo-bot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/todo-bot/ .

# Create non-root user for security
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Expose health check port
EXPOSE 8082

# Run the bot rev 1
CMD ["python", "app.py"]
