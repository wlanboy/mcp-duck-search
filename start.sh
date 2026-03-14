docker network create mcp-net 2>/dev/null || true

docker pull searxng/searxng

docker stop searxng || true
docker rm searxng || true

docker run -d --name searxng \
  --network mcp-net \
  -p 8880:8080 \
  -v ./searxng:/etc/searxng \
  searxng/searxng

docker stop mcp-duck || true
docker rm  mcp-duck || true

docker build -t mcp-duck-search .
docker run -d --name mcp-duck \
  --network mcp-net \
  -p 9900:9900 \
  -e SEARXNG_URL=http://searxng:8080 \
  mcp-duck-search