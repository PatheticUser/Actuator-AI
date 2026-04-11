"""
01_hello_agent/agent.py — The Simplest Possible Agent

Concepts: Agent, Runner, function_tool, multi-turn conversation
Run:      uv run agent.py
"""

import sys
import os 
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents import Agent, Runner, function_tool

from shared.models.ollama_provider import get_model


@function_tool
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}! Welcome to Agentic AI Hub!"


agent = Agent(
    name="Hello Agent",
    instructions="You are a friendly greeter. Use the greet tool when someone tells you their name. Be warm and concise.",
    model=get_model(),
    # model=get_model("minimax-m2.7:cloud"),
    tools=[greet],
)


async def main():
    # Single turn
    result = await Runner.run(agent, "Hi! My name is Ahmad.")
    print(result.final_output)

    # # Multi-turn
    # new_input = result.to_input_list() + [{"role": "user", "content": "What can you help me with?"}]
    # result = await Runner.run(agent, new_input)
    # print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
