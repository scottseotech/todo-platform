#!/bin/bash
set -euo pipefail

todops loki search error --since "15 minutes ago" | \
logmine -dhp | \
tr '\n' '\0' | \
xargs -0 -n1 -I{} todops slack post-message alerts --code "{}"