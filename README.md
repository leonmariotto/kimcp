# KiCad MCP server.

## About

This is a MCP server that provide some tools for PCB design.
It is intended to provide ONLY pcb (board) tools.

Here's the following tools that is provided :
- get_footprint_bitmap:
    This tool should enable the agent to know where is oriented each pin
    of the footprint in its original rotation.
    input: footprint id (schematic id?)
    output: footprint bitmap (to be defined)
- get_footprint_pos:
    input: footprint id (schematic id?)
    output: (pos_x, pos_y, rotation)
- set_footprint_pos:
    input: footprint id (schematic id?) (pos_x, pos_y, rotation)
    output: OK, error
- get_board_coord:
    input: 
    output: ((x,y),(x,y),(x,y),(x,y))
- set_board_coord:
    input: ((x,y),(x,y),(x,y),(x,y))
    output: OK, error

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


- Implement the tools
- Rework the uv integration with a `uv tool install`
- Do the entrypoint in kimcp.py
