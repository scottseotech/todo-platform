#!/bin/bash
set -euo pipefail

echo "LOKI_URL=${LOKI_URL}"
ecoh "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}"

todops loki search error --since "15 minutes ago" | \
logmine -dhp | \
tr '\n' '\0' | \
xargs -0 -n1 -I{} todops slack post-message alerts --code "{}"