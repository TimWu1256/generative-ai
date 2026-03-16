import base64

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from agents.utils.llm_factory import create_chat_model

def create_audio_node(
    model: str = "gemini-2.5-flash",
    temperature: float = 0.0,
    provider: str | None = None,
):
    llm = create_chat_model(model=model, temperature=temperature, provider=provider)

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

    def audio_node(state) -> Command[str]:
        result = audio_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    AIMessage(content=result["messages"][-1].content, name="audio_agent")
                ]
            },
            goto="supervisor",
        )

    return audio_node


audio_node = create_audio_node()
