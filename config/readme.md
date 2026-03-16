# Agent Node Config

This project supports config-driven worker mounting for the supervisor graph.

## File

- `config/agent_nodes.toml`

## Quick Start

1. Add a worker entry under `[[nodes]]`.
2. Set `name` to the node name used by the supervisor.
3. Set `adapter = "python"`.
4. Set `callable` to your Python path in this format:
   - `package.module:symbol`
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
| `adapter`       | string  | yes      | —         | Adapter type. Currently only `"python"` is supported.                       |
| `callable`      | string  | yes      | —         | Python import path in `package.module:symbol` format (see below).           |
| `callable_type` | string  | no       | `"node"`  | How the callable is used. See **callable_type options** below.              |
| `model`         | string  | no       | `null`    | LLM model name passed to the node factory. Only used when `callable_type = "factory"`. |
| `temperature`   | float   | no       | `null`    | Sampling temperature passed to the node factory. Only used when `callable_type = "factory"`. |
| `provider`      | string  | no       | `null`    | Force provider (`google`, `openai`, `anthropic`). If omitted, inferred from `model`. Only used when `callable_type = "factory"`. |
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
```

## Notes

- Disable a node without code changes by setting `enabled = false`.
- Keep node names unique.
- Factory callables must return a node function that routes back to `"supervisor"`.
