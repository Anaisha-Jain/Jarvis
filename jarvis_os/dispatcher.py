"""
Jarvis Data Analyst - Dispatcher

This is the piece that plugs into your main Jarvis orchestrator (the LLM
that parses spoken intent into structured actions). It defines:

  1. TOOLS       - the JSON schema you hand to the LLM's function-calling API
  2. handle_action - takes the LLM's structured output and executes it

Everything in this module is RISK TIER: LOW -> auto-executes, no
confirmation gate needed. This is intentional: nothing here reads/writes
local files, sends messages, or deletes anything.

When you build the File & App Commander or Digital Twin modules, give
each action a "risk" field and route "high" risk actions through a
confirmation state machine BEFORE calling their handlers. This dispatcher
is a template for that pattern too.
"""
from stocks import get_stock_summary, get_portfolio_summary
from weather import get_weather_summary
from research import deep_research

# ---------------------------------------------------------------------------
# 1. Tool schema - hand this list to your LLM's function-calling API
#    (Ollama's tool-calling API, in this build - see orchestrator.py)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_stock_price",
        "description": "Get the current price and daily performance of a stock ticker.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. AAPL, TSLA, MSFT",
                }
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_watchlist",
        "description": "Get a quick performance summary for multiple stock tickers at once.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ticker symbols",
                }
            },
            "required": ["tickers"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get current weather conditions for a location.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name, e.g. 'Toronto' or 'Willowdale, Ontario'",
                }
            },
            "required": ["location"],
        },
    },
   {
        "name": "deep_research",
        "description": (
            "Search the web, read the top sources on a topic, and produce a spoken-friendly briefing. "
            "Use for open-ended research requests. The user's query or area of interest MUST be captured "
            "entirely inside the 'topic' argument."
        ),
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string", 
                    "description": "The exact research topic, question, or search query extracted from the user's input."
                },
                "num_sources": {
                    "type": "integer",
                    "description": "How many sources to pull (default 5)",
                },
            },
            "required": ["topic"],
        },
    },
]


# ---------------------------------------------------------------------------
# 2. Dispatcher - executes a structured action produced by the LLM
# ---------------------------------------------------------------------------

def handle_action(action: dict) -> str:
    """
    action example:
        {"name": "get_stock_price", "input": {"ticker": "AAPL"}}

    Returns a spoken-ready string. Never raises to the caller - errors are
    converted into a spoken apology so Jarvis degrades gracefully instead
    of crashing mid-conversation.
    """
    name = action.get("name")
    params = action.get("input", {})

    try:
        if name == "get_stock_price":
            return get_stock_summary(params["ticker"]).spoken_summary()

        if name == "get_watchlist":
            summaries = get_portfolio_summary(params["tickers"])
            if not summaries:
                return "I couldn't resolve any of those tickers, Sir."
            return " ".join(s.spoken_summary() for s in summaries)

        if name == "get_weather":
            return get_weather_summary(params["location"]).spoken_summary()

        if name == "deep_research":
            topic = params.get("topic") or next(iter(params.values()), None) if params else None
            if not topic:
                return "I couldn't isolate a research topic from that request, Sir."

            num_src = params.get("num_sources")
            if num_src is not None:
                try:
                    # 1. First, check if it's already a digit string like "10"
                    if isinstance(num_src, str) and num_src.isdigit():
                        num_src = int(num_src)
                    # 2. Next, check if it's a word string like "ten"
                    elif isinstance(num_src, str):
                        from word2number import w2n
                        num_src = w2n.word_to_num(num_src)
                    # 3. Otherwise, force cast it directly
                    else:
                        num_src = int(num_src)
                except (ValueError, TypeError):
                    num_src = None  # Safe fallback if it's pure garbage

            report = deep_research(str(topic), num_sources=num_src)
            return report.spoken_summary()
        return f"I don't have a handler for '{name}' yet, Sir."

    except Exception as e:
        return f"I ran into a problem with that request, Sir: {e}"