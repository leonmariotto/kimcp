# KiCad MCP server.

## About

This is a MCP server that provide some tools for PCB design.
It is intended to provide ONLY pcb (board) tools.

## Codex

The following config.toml configuration has been used to connect successfully
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

- Rework the uv integration with a `uv tool install`
- Do the entrypoint in kimcp.py
- Implement a query mechanism of get_footprints (described in tools commentary)
