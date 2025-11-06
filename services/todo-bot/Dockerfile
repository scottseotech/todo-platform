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

# Install sudo and create non-root user for security
RUN apt-get update && \
    apt-get install -y sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 botuser && \
    echo "botuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown -R botuser:botuser /app

RUN <<EOF
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
	&& sudo mkdir -p -m 755 /etc/apt/keyrings \
        && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& sudo apt update \
	&& sudo apt install gh -y
EOF

USER botuser

# OpenTelemetry configuration
ENV OTEL_ENABLED=true
ENV OTEL_SERVICE_NAME=todo-bot
ENV OTEL_EXPORTER_OTLP_ENDPOINT=tempo:4317
ENV OTEL_EXPORTER_OTLP_INSECURE=true
ENV OTEL_ENABLE_STDOUT=false

# Expose health check port
EXPOSE 8082

# Run the bot rev 1
CMD ["python", "app.py"]
