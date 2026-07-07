import argparse
import sys
from dispatcher import handle_action
import re
import dispatcher

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

    p_mkdir = sub.add_parser("mkdir", help="Create a directory")
    p_mkdir.add_argument("path")

    p_mkword = sub.add_parser("mkword", help="Create a Word document")
    p_mkword.add_argument("path")

    p_mkfile = sub.add_parser("mkfile", help="Create a file")
    p_mkfile.add_argument("path")

    p_rmdir = sub.add_parser("rmdir", help="Delete a directory")
    p_rmdir.add_argument("path")

    p_launch = sub.add_parser("launch", help="Launch a local application")
    p_launch.add_argument("app_name")
    p_launch.add_argument("--query", help="Optional search query for the app")

    p_open = sub.add_parser("open", help="Open a website URL")
    p_open.add_argument("url")

    p_playback = sub.add_parser("playback_control", help="Control music playback")
    p_playback.add_argument("--action", choices=["play_pause", "next", "previous"], help="Action to perform")

    p_volume = sub.add_parser("volume", help="Control Spotify volume")
    p_volume.add_argument("direction", choices=["up", "down", "set"])
    p_volume.add_argument("--level", type=float, default=0.5, help="0.0-1.0, only used with 'set'")

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
        action = {"name": "deep_research", "input": {"topic": args.topic, "num_sources": args.sources}}
    elif args.command == "mkdir":
        action = {"name": "create_directory", "input": {"path": args.path}}
    elif args.command == "rmdir":
        action = {"name": "delete_directory", "input": {"path": args.path}}
    elif args.command == "launch":
        action = {"name": "launch_application", "input": {"app_name": args.app_name, "query": args.query}}
    elif args.command == "open":
        action = {"name": "open_website", "input": {"url": args.url}}
    elif args.command == "mkfile":
        action = {"name": "create_file", "input": {"path": args.path}}
    elif args.command == "mkword":
        action = {"name": "create_word_doc", "input": {"path": args.path}}
    elif args.command == "whatsapp":
        action = {"name": "send_whatsapp", "input": {"recipient_name": args.recipient_name, "message": args.message}}
    elif args.command == "playback_control":
        action = {"name": "playback_control", "input": {"action": args.action}}
    elif args.command == "volume":
        action = {"name": "set_volume", "input": {"direction": args.direction, "level": args.level}}
    else:
        sys.exit(1)

    print(handle_action(action))


if __name__ == "__main__":
    main()
