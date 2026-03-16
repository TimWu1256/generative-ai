# -------------------------------------------------------------
# Config setup
# -------------------------------------------------------------

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# Instantiate the model
# -------------------------------------------------------------

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# -------------------------------------------------------------
# Define the Supervisor Node
# -------------------------------------------------------------

from typing import Literal
from typing_extensions import TypedDict
from langgraph.types import Command
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents.image_agent import image_node
from agents.audio_agent import audio_node
from agents.video_agent import video_node

members = ["image_agent", "audio_agent", "video_agent"]
options = members + ["FINISH"]

system_prompt =  (
    f"""You are a supervisor tasked with managing a conversation between the following workers: {members}. \
        Given the following user request, respond with the worker to act next. \
        Each worker will perform a task and respond with their results and status.
    """
)

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*options]

class State(MessagesState):
    """State with next variable for routing and completed_agents to track which agents have responded."""
    next: str
    completed_agents: set = set()

def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    """
    Supervisor node that routes to the next agent based on the response.

    Returns:
        Command: command to update the state and route to the next agent.
    """

    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)

    # Check the messages to see which agents have already responded
    goto = response["next"]
    combined_response = []
    completed_agents = set()

    for message in state.get("messages", []):
        if isinstance(message, AIMessage) and message.name:
            completed_agents.add(message.name)
            combined_response.append(message)

    # Summarize the responses from all agents when all agents have responded
    if len(list(completed_agents)) == len(members):
        human_message = ""
        for message in state.get("messages", []):
            if isinstance(message, HumanMessage):
                human_message = message.content

        summarize_prompt = (
            f"""
            You are a decision agent. Summarize based on all {len(members)} response from the agents \
            and return the final decision for the input prompt question {human_message}.
            """
        )

        messages = ([SystemMessage(content=summarize_prompt)]
                    + combined_response)

        decision_response = llm.invoke(messages)
        return Command(
            update={
                "messages": [
                    decision_response
                ]
        },
            goto=END,
        )

    # ensure all agent is called only once
    elif goto in completed_agents:
        remainders = set(members) - completed_agents
        if remainders:
            goto = list(remainders)[0]
        else:
            goto = END

    return Command(goto=goto, update={"next": goto, "completed_agents": completed_agents})

# -------------------------------------------------------------
# Build Graph
# -------------------------------------------------------------

graph = StateGraph(State)
graph.add_node("supervisor", supervisor_node)
graph.add_node("image_agent", image_node)
graph.add_node("audio_agent", audio_node)
graph.add_node("video_agent", video_node)

graph.add_edge(START, "supervisor")
agent = graph.compile()

# see the current graph structure
png_bytes = agent.get_graph().draw_mermaid_png()
# from IPython.display import Image, display
# display(Image(png_bytes))
with open("graph.png", "wb") as f:
    f.write(png_bytes)

# build the graph
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
react_graph_memory = graph.compile(checkpointer=memory)
