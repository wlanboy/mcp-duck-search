docker stop  mcp-duck-search  || true
docker rm  mcp-duck-search  || true

docker build -t mcp-duck-search .
docker run -d --name mcp-duck -p 9900:9900 mcp-duck-search