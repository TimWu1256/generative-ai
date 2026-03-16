import base64

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from agents.utils.llm_factory import create_chat_model

def create_image_node(
    model: str = "gemini-2.5-flash",
    temperature: float = 0.0,
    provider: str = "google",
):
    llm = create_chat_model(model=model, temperature=temperature, provider=provider)

    def load_image(question: str, imagepath: str) -> str:
        """Answer a user question from a local image file."""
        with open(imagepath, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": f"{question} Also explain your reasoning"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    },
                ]
            )
        ]

        response = llm.invoke(messages)
        return response.content

    image_agent = create_react_agent(
        llm,
        tools=[load_image],
        prompt=(
            "You are image_agent and an expert at detecting objects in images. "
            "Only provide answer to the image file. You must use a tool in every response. "
            "Do not answer directly. Always reason step by step and invoke a tool"
        ),
    )

    def image_node(state) -> Command[str]:
        result = image_agent.invoke(state)
        return Command(
            update={
                "messages": [
                    AIMessage(content=result["messages"][-1].content, name="image_agent")
                ]
            },
            goto="supervisor",
        )

    return image_node
