# Source: https://github.com/actions/runner/pkgs/container/actions-runner
FROM ghcr.io/actions/actions-runner:latest

# Install dependencies
RUN sudo apt-get update && \
    DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
    python3-dev \
    libpq-dev \
    && sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*

COPY --chmod=555 scripts/tools.sh           /usr/local/bin/
RUN tools.sh