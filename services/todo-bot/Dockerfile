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

# Create non-root user for security
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Expose health check port
EXPOSE 8082

# Run the bot rev 1
CMD ["python", "app.py"]
