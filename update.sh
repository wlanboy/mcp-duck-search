#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

git pull

docker build -t mcp-duck-search .

docker stop mcp-duck || true
docker rm mcp-duck || true

docker run -d --name mcp-duck \
  --restart always \
  -p 9900:9900 \
  mcp-duck-search
