FROM python:3.11-slim

WORKDIR /app

# Copy todo-client-python first for better layer caching
RUN cp -r ../../clients/todo-client-python /tmp/todo-client-python

# Install todo-client
RUN pip install --no-cache-dir /tmp/todo-client-python && rm -rf /tmp/todo-client-python

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Expose health check port
EXPOSE 8080

# Run the bot
CMD ["python", "app.py"]
