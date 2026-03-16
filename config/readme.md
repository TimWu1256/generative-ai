# Agent Node Config

This project supports config-driven worker mounting for the supervisor graph.

## File

- `config/agent_nodes.toml`

## Quick Start

1. Add a worker entry under `[[nodes]]`.
2. Set `name` to the node name used by the supervisor.
3. Set `adapter` to one of `"python"`, `"mcp"`.
4. Fill required fields for that adapter.
5. Set `enabled = true`.
6. Restart the service.

## Agent Contract (What You Must Implement)

This section defines the minimum contract your agent must follow to be plug-and-play in this framework.

### 1) Python adapter (`adapter = "python"`)

Your `callable` must point to a **factory function** that returns a LangGraph node callable.

- Factory signature (required):

```python
def create_xxx_node(
      model: str,
      provider: str,
      temperature: float = 0.0,
):
      ...
      def xxx_node(state) -> Command[str]:
            ...
            return Command(
                  update={
                        "messages": [AIMessage(content="...", name="xxx_agent")]
                  },
                  goto="supervisor",
            )
      return xxx_node
```

- Required behavior:
   - Must return a callable node function.
   - Node function must return `Command`.
   - `goto` should route back to `"supervisor"`.
   - Node should append one `AIMessage` with `name` set to your node name (recommended for supervisor tracking).

- Runtime injection:
   - `model`, `provider`, and optional `temperature` come from `config/agent_nodes.toml`.

### 2) MCP adapter (`adapter = "mcp"`)

Your MCP server (SSE transport) must expose a tool (default `run_agent`) that accepts this payload shape:

```json
{
   "messages": [...],
   "state": {...}
}
```

Tool output should include text content; runtime will extract textual fields and route result back to supervisor.

## Parameter Reference

### `[supervisor]` section

| Parameter     | Type   | Required | Description                                      |
|---------------|--------|----------|--------------------------------------------------|
| `model`       | string | yes      | LLM model name for the supervisor routing agent. |
| `temperature` | float  | yes      | Sampling temperature for the supervisor LLM.     |
| `provider`    | string | yes      | LLM provider (`google`, `openai`, `anthropic`). |

### `[[nodes]]` section (one per worker agent)

| Parameter       | Type    | Required | Default   | Description                                                                 |
|-----------------|---------|----------|-----------|-----------------------------------------------------------------------------|
| `name`          | string  | yes      | —         | Unique node name. Must match the routing keys used by the supervisor.        |
| `adapter`       | string  | yes      | —         | Adapter type: `"python"`, `"mcp"`.                                      |
| `callable`      | string  | no       | `null`    | Python import path in `package.module:symbol` format. Required when `adapter = "python"`. |
| `model`         | string  | conditional | `null`    | Required when `adapter = "python"`. Passed into the Python factory callable. |
| `temperature`   | float   | no       | `null`    | Optional. Passed into the Python factory callable. |
| `provider`      | string  | conditional | `null`    | Required when `adapter = "python"`. Allowed values: `google`, `openai`, `anthropic`. |
| `timeout_sec`   | float   | no       | `30.0`    | Request timeout for `mcp` calls in seconds.                                |
| `mcp_url`       | string  | conditional | `null`    | SSE endpoint URL of remote MCP server. Required when `adapter = "mcp"`.    |
| `mcp_headers`   | table   | no       | `null`    | Optional HTTP headers for SSE connection (for example Authorization).      |
| `mcp_sse_read_timeout` | float | no | `300.0` | SSE stream read timeout in seconds.                                         |
| `mcp_tool`      | string  | no       | `"run_agent"` | MCP tool name to invoke. Used when `adapter = "mcp"`.                   |
| `enabled`       | boolean | no       | `true`    | Set to `false` to disable the node without removing it from the config.     |

### `callable` path format

```
package.module:symbol
```

- `package.module` — the dotted Python import path relative to the project root.
- `symbol` — the function or object to import from that module.

**Examples:**
```
agents.image_agent:create_image_node
my_team.custom_agent:create_node
```

### MCP adapter

- Set `adapter = "mcp"`.
- Required field: `mcp_url`.
- Optional: `mcp_headers`, `mcp_sse_read_timeout`, `mcp_tool`, `timeout_sec`.
- Current transport is SSE remote MCP server.

## Example

```toml
[supervisor]
model = "gemini-2.5-flash"
temperature = 0.7
provider = "google"

# A factory node — model and temperature are injected from config
[[nodes]]
name = "my_custom_agent"
adapter = "python"
callable = "my_team_agents.custom:create_my_custom_node"
model = "gemini-2.5-flash"
temperature = 0.0
provider = "google"
enabled = true

# An MCP external agent (SSE remote)
[[nodes]]
name = "external_mcp_agent"
adapter = "mcp"
mcp_url = "https://third-party.example.com/mcp/sse"
# mcp_headers = { Authorization = "Bearer <token>" }
mcp_tool = "run_agent"
timeout_sec = 20
enabled = false
```

## Notes

- Disable a node without code changes by setting `enabled = false`.
- Keep node names unique.
- `provider` values are validated at startup. Allowed: `google`, `openai`, `anthropic`.
- For `adapter = "python"`, `callable` must point to a factory callable.
- For `adapter = "python"`, both `model` and `provider` are required.
- Python factory callables must return a node function that routes back to `"supervisor"`.

## Minimal Python Agent Template

Use this template when onboarding a new Python worker:

```python
from langchain_core.messages import AIMessage
from langgraph.types import Command

from agents.utils.llm_factory import create_chat_model


def create_my_agent_node(model: str, provider: str, temperature: float = 0.0):
   llm = create_chat_model(model=model, provider=provider, temperature=temperature)

   def my_agent_node(state) -> Command[str]:
      # Replace with your own logic/tool calls.
      result_text = "your result"
      return Command(
         update={"messages": [AIMessage(content=result_text, name="my_agent")]},
         goto="supervisor",
      )

   return my_agent_node
```
