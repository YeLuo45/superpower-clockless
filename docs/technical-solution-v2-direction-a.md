# Technical Solution V2 Direction A

## Architecture

```
Agent MCP client
  -> superpower-clockless mcp
    -> superpower_clockless.mcp_server.SuperpowerMCPServer
      -> superpower_clockless.api_client.SuperpowerClient
        -> ai-superpower REST API (/api/projects, /api/proposals)
```

## API Client

`SuperpowerClient` uses Python stdlib `urllib.request` only. It reads defaults from:

- `AI_SUPERPOWER_URL`, default `http://127.0.0.1:8000`
- `AI_SUPERPOWER_API_KEY`, required for authenticated calls unless provided by constructor

The client keeps request construction testable by exposing narrow methods instead of forcing every caller to handcraft URLs.

## MCP Bridge

The bridge implements the JSON-RPC subset required by common MCP clients:

- `initialize`
- `tools/list`
- `tools/call`
- notifications are ignored without output

Each tool returns `content: [{type: "text", text: "...json..."}]` so agents can consume structured API responses without transport-specific dependencies.

## Error Handling

- Missing API key raises `SuperpowerAPIError` before network calls.
- HTTP errors include status code and response body.
- MCP tool errors are returned as `isError: true` JSON-RPC results instead of crashing the stdio process.
- Unknown JSON-RPC methods return `-32601`.

## Test Strategy

- Unit test API request construction using a fake opener.
- Unit test MCP method handling with a fake client.
- CLI test ensures `mcp-info` prints metadata and `mcp` remains callable via parser path.
- Existing installer tests protect cross-agent config behavior.

## Deployment

No deployment build step is needed. GitHub Pages continues to serve `site/` via workflow mode.
