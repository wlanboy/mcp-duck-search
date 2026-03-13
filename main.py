from search import mcp

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=9900, path="/sse")
