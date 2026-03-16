from __future__ import annotations

import asyncio
import importlib
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.types import Command


def _state_to_payload(state: dict[str, Any]) -> dict[str, Any]:
    messages = state.get("messages", [])
    serialized_messages = []
    for message in messages:
        if isinstance(message, BaseMessage):
            serialized_messages.append(
                {
                    "type": message.type,
                    "name": getattr(message, "name", None),
                    "content": message.content,
                }
            )
        else:
            serialized_messages.append(str(message))

    return {
        "messages": serialized_messages,
        "state": {k: v for k, v in state.items() if k != "messages"},
    }


def _extract_text_from_mcp_result(result: Any) -> str:
    content_items = getattr(result, "content", None)
    if content_items is None and isinstance(result, dict):
        content_items = result.get("content")

    if isinstance(content_items, list):
        chunks: list[str] = []
        for item in content_items:
            text = getattr(item, "text", None)
            if text is None and isinstance(item, dict):
                text = item.get("text")
            if text is None:
                text = str(item)
            chunks.append(str(text))
        return "\n".join(chunks).strip()

    if isinstance(result, dict):
        for key in ("content", "output", "response", "text", "message"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value

    return str(result)


async def _call_mcp_streamable_http(
    *,
    url: str,
    tool_name: str,
    payload: dict[str, Any],
    timeout_sec: float,
    headers: dict[str, str] | None,
    read_timeout: float,
) -> Any:
    try:
        mcp_module = importlib.import_module("mcp")
        mcp_http_module = importlib.import_module("mcp.client.streamable_http")
        ClientSession = getattr(mcp_module, "ClientSession")
        streamablehttp_client = getattr(mcp_http_module, "streamablehttp_client")
    except (ImportError, AttributeError) as exc:
        raise ImportError(
            "MCP adapter requires package 'mcp'. Install it with: pip install mcp"
        ) from exc

    async with streamablehttp_client(
        url=url,
        headers=headers,
        timeout=timeout_sec,
        sse_read_timeout=read_timeout,
    ) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            return await asyncio.wait_for(
                session.call_tool(tool_name, payload),
                timeout=timeout_sec,
            )


def create_mcp_node(
    *,
    node_name: str,
    url: str,
    tool_name: str = "run_agent",
    timeout_sec: float = 30.0,
    headers: dict[str, str] | None = None,
    read_timeout: float = 300.0,
) -> Any:
    async def mcp_node(state) -> Command[str]:
        payload = _state_to_payload(state)
        result = await _call_mcp_streamable_http(
            url=url,
            tool_name=tool_name,
            payload=payload,
            timeout_sec=timeout_sec,
            headers=headers,
            read_timeout=read_timeout,
        )
        content = _extract_text_from_mcp_result(result)
        return Command(
            update={"messages": [AIMessage(content=content, name=node_name)]},
            goto="supervisor",
        )

    return mcp_node