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
            "Search the web, read the top sources on a topic, and produce a "
            "spoken-friendly briefing. Use for open-ended research requests."
        ),
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Research topic or question"},
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
            report = deep_research(
                params["topic"], params.get("num_sources")
            )
            return report.spoken_summary()

        return f"I don't have a handler for '{name}' yet, Sir."

    except Exception as e:
        return f"I ran into a problem with that request, Sir: {e}"