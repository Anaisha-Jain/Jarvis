import json
import requests
import config as config
from dispatcher import TOOLS, handle_action
from datetime import datetime
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


from datetime import datetime, timedelta

def route_command(transcript: str) -> str:
    """Main entry point: transcript in, spoken response out."""
    if not transcript.strip():
        return "I didn't catch that, Sir."

    # Calculate exact dates in the strict DD-Mon-YYYY format IMAP requires
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    current_date = today.strftime("%d-%b-%Y")
    yesterday_date = yesterday.strftime("%d-%b-%Y")

    # Highlight system tools explicitly to the model, now with a precise calendar
    messages = [
        {
            "role": "system", 
            "content": (
                f"You are Jarvis, an advanced AI butler. "
                f"Today's date is {current_date}. Yesterday was {yesterday_date}. "
                "The current location is Toronto, Ontario, Canada. "
                "You have access to local system tools. "
                "If the user asks to open a website, launch an app, make/delete directories, "
                "look up stocks/weather, or check emails, you MUST call the appropriate function tool immediately. "
                "Do not just talk about doing it—call the tool. "
                "If the user asks a general knowledge question that has nothing to do with your "
                "tools (like a fun fact, a definition, or general trivia), just answer it directly "
                "in plain spoken language—do not call a tool for it."
            )
        },
        {"role": "user", "content": transcript}
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
                "Do not just talk about doing it—call the tool. "
                "If the user asks a general knowledge question that has nothing to do with your "
                "tools (like a fun fact, a definition, or general trivia), just answer it directly "
                "in plain spoken language—do not call a tool for it."
            )
        },
        {"role": "user", "content": transcript}
    ]

    try:
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
    except requests.exceptions.ConnectionError:
        print("[DEBUG] Could not connect to Ollama -- is it running?")
        return "I can't reach my language model right now, Sir. Is Ollama running?"
    except requests.exceptions.Timeout:
        print("[DEBUG] Ollama request timed out.")
        return "That took too long to process, Sir."
    except requests.exceptions.HTTPError as e:
        print(f"[DEBUG] Ollama returned an error: {e}\nResponse body: {resp.text}")
        return "My language model ran into an error, Sir."

    raw_json = resp.json()
    print(f"\n[DEBUG] Full Ollama response: {json.dumps(raw_json, indent=2)}\n")

    message = raw_json.get("message", {})
    tool_calls = message.get("tool_calls") or []

    if not tool_calls:
        content = (message.get("content") or "").strip()
        if not content:
            print("[DEBUG] Ollama returned no tool call AND no content -- empty response.")
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
                print(f"[DEBUG] Failed to parse tool arguments as JSON: {args}")
                args = {}

        try:
            result = handle_action({"name": name, "input": args})
        except Exception as e:
            print(f"[DEBUG] handle_action raised an exception: {e}")
            result = f"I ran into a problem running that, Sir: {e}"

        results.append(result)
        
    return " ".join(results)