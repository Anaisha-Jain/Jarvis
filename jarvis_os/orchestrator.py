"""
Jarvis Data Analyst - Orchestrator

Turns a raw transcript into a tool call (or a plain spoken reply) using a
local Ollama model. This is the seam between "words Jarvis heard" and
"action Jarvis takes".

Requires Ollama running locally with a tool-calling-capable model pulled
(llama3.1, qwen2.5, and mistral-nemo all support it):

    ollama serve
    ollama pull llama3.1
"""

import json

import requests

import config as config
from dispatcher import TOOLS, handle_action


def _ollama_tools():
    # Ollama's tool-calling API uses OpenAI's function-call format
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }
        for tool in TOOLS
    ]


def route_command(transcript: str) -> str:
    """Main entry point: transcript in, spoken response out."""
    if not transcript.strip():
        return "I didn't catch that, Sir."

    resp = requests.post(
        f"{config.OLLAMA_HOST}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": [{"role": "user", "content": transcript}],
            "tools": _ollama_tools(),
            "stream": False,
        },
        timeout=60,
    )
    resp.raise_for_status()
    message = resp.json().get("message", {})
    tool_calls = message.get("tool_calls") or []

    if not tool_calls:
        content = (message.get("content") or "").strip()
        return content or "I'm not sure how to help with that, Sir."

    results = []
    for call in tool_calls:
        fn = call.get("function", {})
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        results.append(handle_action({"name": fn.get("name"), "input": args}))
    return " ".join(results)