import base64

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from agents.utils.llm_factory import create_chat_model

def create_video_node(
    model: str = "gemini-2.5-flash",
    temperature: float = 0.0,
    provider: str = "google",
):
    llm = create_chat_model(model=model, temperature=temperature, provider=provider)

    def load_video(question: str, filepath: str) -> str:
        """Answer a user question from a local video file."""
        with open(filepath, "rb") as f:
            video_data = base64.b64encode(f.read()).decode("utf-8")

        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": f"{question} Also explain your reasoning"},
                    {"type": "media", "mime_type": "video/mp4", "data": video_data},
                ]
            )
        ]

        response = llm.invoke(messages)
        return response.content

    video_agent = create_react_agent(
        llm,
        tools=[load_video],
        prompt=(
            "You are video_agent and an expert at detecting objects in videos. "
            "Only provide answer to the video file. You must use a tool in every response. "
            "Do not answer directly. Always reason step by step and invoke a tool"
        ),
    )

    def video_node(state) -> Command[str]:
        result = video_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    AIMessage(content=result["messages"][-1].content, name="video_agent")
                ]
            },
            goto="supervisor",
        )

    return video_node
