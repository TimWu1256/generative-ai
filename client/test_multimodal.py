import sys
from pathlib import Path

# Allow running via `python client/test_multimodal.py` from project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.messages import HumanMessage

from agents.supervisor import react_graph_memory


def run_case(thread_id: str, prompt_text: str) -> None:
    config = {"configurable": {"thread_id": thread_id}, "subgraph": True}
    result = react_graph_memory.invoke(
        {
            "messages": [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": prompt_text,
                        }
                    ]
                )
            ]
        },
        config,
    )

    for message in result["messages"]:
        if hasattr(message, "pretty_print"):
            message.pretty_print()
        else:
            print(message)


if __name__ == "__main__":
    positive_prompt = (
        "Question: Can you see dog in these files? Explain your reasoning. "
        "File path: For image_agent, use the image path ./data/dog_yes.jpg. "
        "For audio_agent, use the audio file path ./data/dog_audio_yes.mp3. "
        "For video_agent, use the video file path ./data/dog_video_yes.mp4"
    )

    negative_prompt = (
        "Question: Can you see dog in these files? Explain your reasoning. "
        "For image_agent, use the image path ./data/scenery.jpg. "
        "For audio_agent, use the audio file path ./data/crowd_cheering.mp3. "
        "For video_agent, use the video file path ./data/people_thinking.mp4"
    )

    print("=== Positive dog result ===")
    run_case(thread_id="1", prompt_text=positive_prompt)

    print("\n=== Negative dog result ===")
    run_case(thread_id="3", prompt_text=negative_prompt)
