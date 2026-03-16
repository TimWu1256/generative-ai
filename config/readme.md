# Agent Node Config

This project supports config-driven worker mounting for the supervisor graph.

## File

- `config/agent_nodes.toml`

## Quick Start

1. Add a worker entry under `[[nodes]]`.
2. Set `name` to the node name used by the supervisor.
3. Set `adapter` to one of `"python"`, `"http"`, `"mcp"`.
4. Fill required fields for that adapter.
5. Set `enabled = true`.
6. Restart the service.

## Parameter Reference

### `[supervisor]` section

| Parameter     | Type   | Required | Description                                      |
|---------------|--------|----------|--------------------------------------------------|
| `model`       | string | yes      | LLM model name for the supervisor routing agent. |
| `temperature` | float  | yes      | Sampling temperature for the supervisor LLM.     |
| `provider`    | string | no       | Force provider (`google`, `openai`, `anthropic`). If omitted, inferred from `model`. |

### `[[nodes]]` section (one per worker agent)

| Parameter       | Type    | Required | Default   | Description                                                                 |
|-----------------|---------|----------|-----------|-----------------------------------------------------------------------------|
| `name`          | string  | yes      | —         | Unique node name. Must match the routing keys used by the supervisor.        |
| `adapter`       | string  | yes      | —         | Adapter type: `"python"`, `"http"`, `"mcp"`.                              |
| `callable`      | string  | no       | `null`    | Python import path in `package.module:symbol` format. Required when `adapter = "python"`. |
| `callable_type` | string  | no       | `"node"`  | How the callable is used. See **callable_type options** below.              |
| `model`         | string  | no       | `null`    | LLM model name passed to the node factory. Only used when `callable_type = "factory"`. |
| `temperature`   | float   | no       | `null`    | Sampling temperature passed to the node factory. Only used when `callable_type = "factory"`. |
| `provider`      | string  | no       | `null`    | Force provider (`google`, `openai`, `anthropic`). If omitted, inferred from `model`. Only used when `callable_type = "factory"`. |
| `endpoint`      | string  | no       | `null`    | HTTP target URL. Required when `adapter = "http"`.                          |
| `method`        | string  | no       | `"POST"`  | HTTP method for external call. Used when `adapter = "http"`.                |
| `headers`       | table   | no       | `null`    | HTTP headers table. Used when `adapter = "http"`.                           |
| `timeout_sec`   | float   | no       | `30.0`    | Timeout for `http` and `mcp` calls in seconds.                               |
| `mcp_command`   | string  | no       | `null`    | MCP server command. Required when `adapter = "mcp"`.                        |
| `mcp_args`      | array   | no       | `[]`      | MCP server command arguments. Used when `adapter = "mcp"`.                  |
| `mcp_tool`      | string  | no       | `"run_agent"` | MCP tool name to invoke. Used when `adapter = "mcp"`.                   |
| `mcp_env`       | table   | no       | `null`    | Environment variables passed to MCP server process.                           |
| `enabled`       | boolean | no       | `true`    | Set to `false` to disable the node without removing it from the config.     |

### `callable_type` options

| Value       | When to use                                                                                   | Expected signature                                           |
|-------------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| `"node"`    | The symbol **is** the node function itself. Model is baked into the function at definition time. | `def my_node(state) -> Command: ...`                         |
| `"factory"` | The symbol **returns** a node function. Model and temperature from config are injected at startup. | `def create_node(model, temperature) -> Callable: ...`       |

### `callable` path format

```
package.module:symbol
```

- `package.module` — the dotted Python import path relative to the project root.
- `symbol` — the function or object to import from that module.

**Examples:**
```
agents.image_agent:image_node          # callable_type = "node"
agents.image_agent:create_image_node   # callable_type = "factory"
my_team.custom_agent:create_node       # callable_type = "factory"
```

### HTTP adapter

- Set `adapter = "http"`.
- Required field: `endpoint`.
- Runtime sends a JSON payload with:
   - `messages`: serialized conversation messages
   - `state`: non-message state fields
- Response parsing priority: `content` -> `output` -> `response` -> `text` -> `message`.

### MCP adapter

- Set `adapter = "mcp"`.
- Required field: `mcp_command`.
- Optional: `mcp_args`, `mcp_tool`, `mcp_env`, `timeout_sec`.
- Current transport is stdio MCP server process.

### Provider auto-detection

- If `provider` is not set, runtime infers it from `model` automatically.
- Current inference rules:
   - model contains `gemini` -> `google`
   - model starts with `gpt`, `o1`, `o3` -> `openai`
   - model contains `claude` -> `anthropic`
- If inference fails, set `provider` explicitly.

## Example

```toml
[supervisor]
model = "gemini-2.5-flash"
temperature = 0.7
# provider = "google"  # optional, can be omitted if model is clear

# A factory node — model and temperature are injected from config
[[nodes]]
name = "my_custom_agent"
adapter = "python"
callable = "my_team_agents.custom:create_my_custom_node"
callable_type = "factory"
model = "gemini-2.5-flash"
temperature = 0.0
# provider = "google"  # optional, can be omitted if model is clear
enabled = true

# A plain node — model is hardcoded inside the function
[[nodes]]
name = "my_simple_agent"
adapter = "python"
callable = "my_team_agents.simple:simple_node"
callable_type = "node"
enabled = true

# An HTTP external agent
[[nodes]]
name = "external_http_agent"
adapter = "http"
endpoint = "http://localhost:8080/infer"
method = "POST"
timeout_sec = 20
enabled = false

# An MCP external agent (stdio)
[[nodes]]
name = "external_mcp_agent"
adapter = "mcp"
mcp_command = "python"
mcp_args = ["-m", "my_mcp_server"]
mcp_tool = "run_agent"
timeout_sec = 20
enabled = false
```

## Notes

- Disable a node without code changes by setting `enabled = false`.
- Keep node names unique.
- Factory callables must return a node function that routes back to `"supervisor"`.
