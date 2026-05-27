# Test Cases V2 Direction A

| ID | Area | Scenario | Expected Result |
|----|------|----------|-----------------|
| TC-A1 | API Client | Construct client from environment | URL trims trailing slash and API key is loaded |
| TC-A2 | API Client | List projects with query parameters | GET `/api/projects?...` uses encoded parameters and auth header |
| TC-A3 | API Client | Create proposal | POST `/api/proposals` sends JSON body and returns parsed JSON |
| TC-A4 | API Client | Update proposal status and fields | PUT requests target `/status` and `/fields` endpoints |
| TC-A5 | API Client | HTTP error body is returned | `SuperpowerAPIError` includes status and response text |
| TC-A6 | MCP | Initialize request | Returns protocol version, capabilities, and server info |
| TC-A7 | MCP | tools/list request | Returns all project/proposal tools with schemas |
| TC-A8 | MCP | proposal_create call | Calls API client and returns JSON text payload |
| TC-A9 | MCP | Tool failure | Returns `isError: true` without process crash |
| TC-A10 | CLI | `mcp-info` command | Prints bridge metadata for documentation/debug use |
| TC-A11 | Regression | Installer behavior | Existing Hermes/Cursor/Codex/Claude install tests remain green |

Acceptance threshold: 100% test pass rate and >=90% coverage.
