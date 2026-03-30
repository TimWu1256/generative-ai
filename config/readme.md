# Agent Node Config

This project supports config-driven worker mounting for the supervisor graph.

## File

- `config/agent_nodes.toml`

## Quick Start

1. Add a worker entry under `[[nodes]]`.
2. Set `name` to the node name used by the supervisor.
3. Set `adapter` to `"python"`.
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

## Parameter Reference

### `[supervisor]` section

| Parameter     | Type   | Required | Description                                      |
|---------------|--------|----------|--------------------------------------------------|
| `model`       | string | yes      | LLM model name for the supervisor routing agent. |
| `temperature` | float  | yes      | Sampling temperature for the supervisor LLM.     |
| `provider`    | string | yes      | LLM provider (`google`, `openai`). |

### `[[nodes]]` section (one per worker agent)

| Parameter       | Type    | Required | Default   | Description                                                                 |
|-----------------|---------|----------|-----------|-----------------------------------------------------------------------------|
| `name`          | string  | yes      | —         | Unique node name. Must match the routing keys used by the supervisor.        |
| `adapter`       | string  | yes      | —         | Adapter type: `"python"`.                                      |
| `callable`      | string  | no       | `null`    | Python import path in `package.module:symbol` format. Required when `adapter = "python"`. |
| `model`         | string  | conditional | `null`    | Required when `adapter = "python"`. Passed into the Python factory callable. |
| `temperature`   | float   | no       | `null`    | Optional. Passed into the Python factory callable. |
| `provider`      | string  | conditional | `null`    | Required when `adapter = "python"`. Allowed values: `google`, `openai`. |
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
```

## Notes

- Disable a node without code changes by setting `enabled = false`.
- Keep node names unique.
- `provider` values are validated at startup. Allowed: `google`, `openai`.
- For `adapter = "python"`, `callable` must point to a factory callable.
-- For `adapter = "python"`, both `model` and `provider` are required.
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
