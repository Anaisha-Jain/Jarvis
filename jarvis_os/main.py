import argparse
import sys

from dispatcher import handle_action

import re

# In main.py
def clean_spoken_text(text: str) -> str:
    text = re.sub(r'\s*at\s*the\s*rate\s*', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*at\s*rate\s*', '@', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*therate\s*', '@', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\s*dot\s*com', '.com', text, flags=re.IGNORECASE)
    
    text = re.sub(r'(\w+)\s*@\s*(\w+)', r'\1@\2', text)
    
    return text

def main():
    parser = argparse.ArgumentParser(description="Jarvis Data Analyst CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # Core tools
    p_stock = sub.add_parser("stock")
    p_stock.add_argument("ticker")

    p_whatsapp = sub.add_parser("whatsapp")
    p_whatsapp.add_argument("recipient_name")
    p_whatsapp.add_argument("message")

    p_watch = sub.add_parser("watchlist")
    p_watch.add_argument("tickers", nargs="+")

    p_weather = sub.add_parser("weather")
    p_weather.add_argument("location")

    p_research = sub.add_parser("research")
    p_research.add_argument("topic")
    p_research.add_argument("--sources", type=int, default=None)

    # System & Web tools
    p_mkdir = sub.add_parser("mkdir", help="Create a directory")
    p_mkdir.add_argument("path")

    p_rmdir = sub.add_parser("rmdir", help="Delete a directory")
    p_rmdir.add_argument("path")

    p_launch = sub.add_parser("launch", help="Launch a local application")
    p_launch.add_argument("app_name")

    p_open = sub.add_parser("open", help="Open a website URL")
    p_open.add_argument("url")

    # Voice pipeline (Declared ONLY once here at the bottom)
    sub.add_parser("listen", help="Start the always-on voice pipeline")

    args = parser.parse_args()

    if args.command == "listen":
        from voice import JarvisVoiceSession
        JarvisVoiceSession().run()
        return

    # Route arguments to actions
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
    elif args.command == "mkdir":
        action = {"name": "create_directory", "input": {"path": args.path}}
    elif args.command == "rmdir":
        action = {"name": "delete_directory", "input": {"path": args.path}}
    elif args.command == "launch":
        action = {"name": "launch_application", "input": {"app_name": args.app_name}}
    elif args.command == "open":
        action = {"name": "open_website", "input": {"url": args.url}}
    # In main.py, inside the route arguments section
    elif args.command == "whatsapp":
        action = {
            "name": "send_whatsapp", 
            "input": {"recipient_name": args.recipient_name, "message": args.message}
        }
    else:
        sys.exit(1)

    print(handle_action(action))


if __name__ == "__main__":
    main()
