import json

import requests

import config as config
from dispatcher import TOOLS, handle_action


import re

def clean_spoken_text(text: str) -> str:
    text = re.sub(r'\s*at\s*the\s*rate\s*', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*at\s*rate\s*', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*therate\s*', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*dot\s*com', '.com', text, flags=re.IGNORECASE)
    
    text = re.sub(r'(\w+)\s*@\s*(\w+)', r'\1@\2', text)
    
    return text

def _ollama_tools():
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

    # Highlight system tools explicitly to the model
    messages = [
        {
            "role": "system", 
            "content": (
                "You are Jarvis, an advanced AI butler. You have access to local system tools. "
                "If the user asks to open a website, launch an app, make/delete directories, "
                "or look up stocks/weather, you MUST call the appropriate function tool immediately. "
                "Do not just talk about doing it—call the tool."
            )
        },
        {"role": "user", "content": transcript}
    ]

    resp = requests.post(
        f"{config.OLLAMA_HOST}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": messages,
            "tools": _ollama_tools(),
            "stream": False,
        },
        timeout=60,
    )
    resp.raise_for_status()
    # ... rest of your original orchestrator logic continues below ...
    message = resp.json().get("message", {})
    tool_calls = message.get("tool_calls") or []

    if not tool_calls:
        content = (message.get("content") or "").strip()
        return content or "I'm not sure how to help with that, Sir."



    results = []
    for call in tool_calls:
        fn = call.get("function", {}) if isinstance(call, dict) else {}
        
        print(f"\n[DEBUG] Ollama Call: {fn}\n")

        args = fn.get("arguments", {})
        name = fn.get("name")
        
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}

        results.append(handle_action({"name": name, "input": args}))
        
    return " ".join(results)