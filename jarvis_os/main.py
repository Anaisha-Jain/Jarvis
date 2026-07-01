"""
Jarvis Data Analyst - CLI test harness

Lets you exercise stocks / weather / research without the voice pipeline
being built yet. Once STT/TTS exists, `handle_action()` from dispatcher.py
is the only thing that needs to be wired in - swap this CLI's input()/print()
for your speech recognizer's transcript and your TTS engine's speak().

Usage:
    python main.py stock AAPL
    python main.py watchlist AAPL TSLA MSFT
    python main.py weather "Toronto"
    python main.py research "solid-state battery breakthroughs 2026"
"""

import argparse
import sys

from dispatcher import handle_action

def main():
    parser = argparse.ArgumentParser(description="Jarvis Data Analyst CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_stock = sub.add_parser("stock")
    p_stock.add_argument("ticker")

    p_watch = sub.add_parser("watchlist")
    p_watch.add_argument("tickers", nargs="+")

    p_weather = sub.add_parser("weather")
    p_weather.add_argument("location")

    p_research = sub.add_parser("research")
    p_research.add_argument("topic")
    p_research.add_argument("--sources", type=int, default=None)

    sub.add_parser("listen", help="Start the always-on voice pipeline")

    args = parser.parse_args()

    if args.command == "listen":
        from voice import JarvisVoiceSession
        JarvisVoiceSession().run()
        return

    if args.command == "stock":
        action = {"name": "get_stock_price", "input": {"ticker": args.ticker}}
    elif args.command == "watchlist":
        action = {"name": "get_watchlist", "input": {"tickers": args.tickers}}
    elif args.command == "weather":
        action = {"name": "get_weather", "input": {"location": args.location}}
    elif args.command == "research":
        action = {
            "name": "deep_research",
            "input": {"topic": args.topic, "num_sources": args.sources},
        }
    else:
        sys.exit(1)

    print(handle_action(action))


if __name__ == "__main__":
    main()
