# KiCad MCP server.

## Codex

The following config.toml configuraiton has been used to connect successfully
to server :
```
[mcp_servers.kimcp]
url = "http://localhost:8000/mcp"
http_headers = { "Accept" = "application/json, text/event-stream" }
startup_timeout_sec = 5
tool_timeout_sec = 5
enabled = true
```

## Curl

Some curl command can be used to verify server is up. A script is available in
scripts/curl.sh.

## TODO


