import base64
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


def load_audio(question: str, filepath: str) -> str:
    """Answer a user question from a local audio file."""
    with open(filepath, "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")

    messages = [
        HumanMessage(
            content=[
                {"type": "text", "text": f"{question} Also explain your reasoning"},
                {"type": "media", "mime_type": "audio/mpeg", "data": audio_data},
            ]
        )
    ]

    response = llm.invoke(messages)
    return response.content


audio_agent = create_react_agent(
    llm,
    tools=[load_audio],
    prompt=(
        "You are audio_agent and an expert at detecting objects in audio files. "
        "Only provide answer to the audio file. You must use a tool in every response. "
        "Do not answer directly. Always reason step by step and invoke a tool"
    ),
)


def audio_node(state) -> Command[Literal["supervisor"]]:
    result = audio_agent.invoke(state)
    return Command(
        update={
            "messages": [
                AIMessage(content=result["messages"][-1].content, name="audio_agent")
            ]
        },
        goto="supervisor",
    )
