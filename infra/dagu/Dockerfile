# syntax=docker/dockerfile:1

# Builder stage for building todops-cli wheel
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy todops-cli source
COPY apps/todops-cli /build/todops-cli

# Build the wheel
RUN cd /build/todops-cli && python3 -m build --wheel

# Final stage
FROM debian:stable-slim

# Install system dependencies (rarely changes - good for caching)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    ca-certificates \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    wget \
    jq \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Create virtual environment (rarely changes - good for caching)
RUN python3 -m venv /opt/venv

# Make virtual environment available in PATH
ENV PATH="/opt/venv/bin:$PATH"

# Install Dagu (rarely changes - good for caching)
RUN DAGU_VERSION=v1.17.4 && \
    curl -fsSL "https://github.com/dagu-org/dagu/releases/download/${DAGU_VERSION}/dagu_${DAGU_VERSION#v}_linux_amd64.tar.gz" -o dagu.tar.gz && \
    tar zxf dagu.tar.gz && \
    mv dagu /usr/local/bin/dagu && \
    chmod +x /usr/local/bin/dagu && \
    rm dagu.tar.gz

WORKDIR /root

# Copy static config files first (change less frequently)
COPY infra/dagu/config.yaml /root/
COPY infra/dagu/dags /dags

# Copy and install todops-cli wheel from builder stage
COPY --from=builder /build/todops-cli/dist/*.whl /tmp/
RUN pip install /tmp/*.whl && rm -rf /tmp/*.whl

# Copy entrypoint (changes most frequently)
COPY infra/dagu/entrypoint.sh /

# Set permissions
RUN chmod +x /entrypoint.sh

EXPOSE 8080

CMD ["/entrypoint.sh"]