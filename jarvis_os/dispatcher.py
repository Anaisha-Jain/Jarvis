import os
import json
import shutil
import smtplib
import imaplib
import email
from email.header import decode_header
from emails import send_email, check_emails_by_date
from datetime import datetime, timedelta
import subprocess
import webbrowser
from docx import Document
from stocks import get_stock_summary, get_portfolio_summary
from weather import get_weather_summary
from research import deep_research
from dotenv import load_dotenv
from calendar_reader import get_todays_schedule
from messaging import send_whatsapp_message
from spotify_control import (
    play_pause, next_track, previous_track,
    system_volume_up, system_volume_down, set_spotify_app_volume,
)

TOOLS = [
    {"name": "create_file", "description": "Create a new empty file at a specified path.", "risk": "low", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "create_directory", "description": "Create a new folder or directory at a specified path.", "risk": "low", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "delete_directory", "description": "Permanently delete an entire directory.", "risk": "high", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "launch_application", "description": "Launch a local system application.", "risk": "medium", "input_schema": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}},
    {"name": "open_website", "description": "Open a specified URL.", "risk": "low", "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "get_stock_price", "description": "Get current stock price.", "risk": "low", "input_schema": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}},
    {"name": "get_watchlist", "description": "Get summary for multiple tickers.", "risk": "low", "input_schema": {"type": "object", "properties": {"tickers": {"type": "array", "items": {"type": "string"}}}, "required": ["tickers"]}},
    {"name": "get_weather", "description": "Get current weather. If the user does not explicitly specify a city, you MUST pass 'Toronto, Ontario' as the location.", "risk": "low", "input_schema": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}},
    {"name": "deep_research", "description": "Search the web for a topic.", "risk": "low", "input_schema": {"type": "object", "properties": {"topic": {"type": "string"}, "num_sources": {"type": "integer"}}, "required": ["topic"]}},
    {"name": "send_email", "description": "Send an email.", "risk": "low", "input_schema": {"type": "object", "properties": {"to_email": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to_email", "subject", "body"]}},
    {"name": "get_upcoming_events", "description": "Retrieve next events.", "risk": "low", "input_schema": {"type": "object", "properties": {"max_results": {"type": "integer"}}}},
    {"name": "check_emails_by_date", "description": "Check inbox for emails.", "risk": "low", "input_schema": {"type": "object", "properties": {"target_day": {"type": "string", "enum": ["today", "yesterday"], "description": "Choose whether to check emails for today or yesterday."}}, "required": ["target_day"]}},
    {"name": "send_text", "description": "Send an SMS message.", "risk": "low", "input_schema": {"type": "object", "properties": {"recipient_name": {"type": "string"}, "message": {"type": "string"}}, "required": ["recipient_name", "message"]}},
    {"name": "create_word_doc", "description": "Create a .docx file.", "risk": "low", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path"]}},
    {"name": "playback_control", "description": "Control Spotify playback: play/pause, next track, previous track.", "risk": "low", "input_schema": {"type": "object", "properties": {"action": {"type": "string", "enum": ["play_pause", "next", "previous"]}}, "required": ["action"]}},
    {"name": "status_report", "description": "Get a complete morning briefing: emails, calendar events, and live system health.", "risk": "low", "input_schema": {"type": "object", "properties": {}}},
    {"name": "set_volume", "description": "Increase, decrease, or set Spotify's volume.", "risk": "low", "input_schema": {"type": "object", "properties": {"direction": {"type": "string", "enum": ["up", "down", "set"]}, "level": {"type": "number", "description": "0.0-1.0, only used when direction is 'set'"}}, "required": ["direction"]}}
]

def handle_action(action):
    name = action.get("name")
    params = action.get("input", {})
    
    try:
        if name == "create_directory":
            path = params.get("path")
            os.makedirs(path, exist_ok=True)
            return f"I have successfully established the directory at {path}, Sir."
            
        # In dispatcher.py
        if name == "open_website":
            url = params.get("url")
            target_url = "https://" + url if not url.startswith("http") else url
            webbrowser.open(target_url)
            return "Right away, Sir."  # Replaced the URL read-out
        
        if name == "status_report":
            import psutil
            from datetime import datetime

            # 1. System Health
            cpu_usage = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            ram_usage = ram.percent

            if cpu_usage > 80:
                health_msg = f"System resources are heavily strained, Sir. CPU is at {cpu_usage} percent."
            else:
                health_msg = f"All systems are operating optimally. CPU is at {cpu_usage} percent, memory at {ram_usage} percent."

            # 2. Emails
            today_date = datetime.now().strftime("%d-%b-%Y")
            email_summary = check_emails_by_date(today_date)

            # 3. Calendar
            calendar_summary = get_todays_schedule()

            return f"{health_msg} {calendar_summary} {email_summary}"
            
        if name == "create_word_doc":
            config_path = 'config.json'
            if not os.path.exists(config_path):
                return "Error: config.json file not found, Sir."
            with open(config_path, 'r') as f:
                config = json.load(f)

            raw_path = params.get("path")
            parts = raw_path.split("/", 1)
            final_path = os.path.join(config.get(parts[0], ""), parts[1]) if len(parts) > 1 and parts[0] in config else raw_path
            
            directory = os.path.dirname(final_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                
            doc = Document()
            doc.add_paragraph(params.get("content", "This is a new document created by Jarvis."))
            doc.save(final_path)
            return f"I have created the Word document at {final_path}, Sir."
        
        if name == "status_report":
            import psutil
            from datetime import datetime
            
            # 1. System Health
            cpu_usage = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            ram_usage = ram.percent
            
            if cpu_usage > 80:
                health_msg = f"System resources are heavily strained, Sir. CPU is at {cpu_usage} percent."
            else:
                health_msg = f"All systems are operating optimally. CPU is at {cpu_usage} percent, memory at {ram_usage} percent."

            # 2. Emails
            today_date = datetime.now().strftime("%d-%b-%Y")
            email_summary = check_emails_by_date(today_date)
            
            # 3. Calendar Placeholder
            calendar_summary = "I don't have access to your live calendar yet, but I am ready to integrate it."

            return f"{health_msg} {email_summary} {calendar_summary}"
        
        if name == "send_email":
            return send_email(
                params.get("to_email"),
                params.get("subject"),
                params.get("body")
            )

        if name == "check_emails_by_date":
            from datetime import datetime, timedelta
            
            target = params.get("target_day", "today").lower()
            
            if target == "yesterday":
                exact_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            else:
                exact_date = datetime.now().strftime("%d-%b-%Y")
                
            return check_emails_by_date(exact_date)

        if name == "delete_directory":
            path = params.get("path")
            if os.path.exists(path):
                shutil.rmtree(path)
                return f"The directory at {path} has been purged, Sir."
            return f"I could not locate a directory at {path}, Sir."
            
        if name == "launch_application":
            import subprocess
            app_input = params.get("app_name").lower()
            
            # Map simple names to full paths
            shortcuts = {
                "excel": "C:/Program Files/Microsoft Office/root/Office16/EXCEL.EXE",
                "word": "C:/Program Files/Microsoft Office/root/Office16/WINWORD.EXE",
                "spotify": "start spotify:",
                "code": "C:/Users/anais/AppData/Local/Programs/Microsoft VS Code/Code.exe"
            }
            
            # Use the shortcut if it exists, otherwise use the input
            app_path = shortcuts.get(app_input, app_input)
            
            try:
                subprocess.Popen(app_path, shell=True)
                return f"Launching {app_input}, Sir."
            except Exception as err:
                return f"I was unable to initialize the application, Sir: {err}"

        if name == "create_file":
            path = params.get("path")
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            with open(path, 'w') as f:
                pass
            return f"I have successfully established the file at {path}, Sir."
        
        if name == "get_stock_price":
            return get_stock_summary(params["ticker"]).spoken_summary()

        if name == "get_watchlist":
            summaries = get_portfolio_summary(params["tickers"])
            return " ".join(s.spoken_summary() for s in summaries) if summaries else "I couldn't resolve those tickers, Sir."
        
        if name == "get_weather":
            location = params.get("location", "")
            
            # Intercept bad LLM guesses and force the correct default location
            if not location or location.lower() in ["here", "current", "my location", "unknown"]:
                location = "Waterloo, Ontario"
                
            return get_weather_summary(location).spoken_summary()
        
        if name == "send_whatsapp":
            return send_whatsapp_message(params["recipient_name"], params["message"])

        if name == "playback_control":
            pb_action = params.get("action")
            if pb_action == "play_pause":
                return play_pause()
            if pb_action == "next":
                return next_track()
            if pb_action == "previous":
                return previous_track()
            return "I don't recognize that playback action, Sir."

        if name == "set_volume":
            direction = params.get("direction")
            level = params.get("level", 0.5)
            
            # If the LLM passes 20 instead of 0.2, fix the math natively
            if level > 1.0:
                level = level / 100.0
                
            if direction == "up":
                return system_volume_up()
            elif direction == "down" and "level" not in params:
                return system_volume_down()
            else:
                # Forces a specific level if one was passed, even if it said "decrease"
                return set_spotify_app_volume(level)

        return f"I don't have a handler for '{name}' yet, Sir."
    
    except Exception as e:
        return f"I ran into a problem with that request, Sir: {e}"