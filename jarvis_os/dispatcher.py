from stocks import get_stock_summary, get_portfolio_summary
from weather import get_weather_summary
from research import deep_research
import os
from dotenv import load_dotenv
from messaging import send_whatsapp_message


TOOLS = [
    {
        "name": "create_directory",
        "description": "Create a new folder or directory at a specified path.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The absolute or relative path where the folder should be created."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "delete_directory",
        "description": "Permanently delete an entire directory/folder and all its contents. Use with caution.",
        "risk": "high",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path of the directory to be destroyed."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "launch_application",
        "description": "Launch a local system application by name (e.g., notepad, calculator).",
        "risk": "medium",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "The name or command executable of the application."}
            },
            "required": ["app_name"],
        },
    },
    {
        "name": "open_website",
        "description": "Open a specified URL or website in the default web browser.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The full web address, e.g., 'https://google.com'"}
            },
            "required": ["url"],
        },
    },
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
    {
        "name": "send_email",
        "description": "Send an email to a recipient with a specific subject and body.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_email": {"type": "string", "description": "The recipient's email address, e.g. 'friend@example.com'"},
                "subject": {"type": "string", "description": "The email subject line"},
                "body": {"type": "string", "description": "The main content of the email"}
            },
            "required": ["to_email", "subject", "body"],
        },
    },
    {
        "name": "get_upcoming_events",
        "description": "Retrieve the next N upcoming events from the user's primary calendar.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Number of events to fetch, defaults to 5"}
            },
        },
    },
    {
        "name": "check_emails_by_date",
        "description": "Check the user's inbox for emails received on a specific target date or phrase like 'today' or 'yesterday'.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_string": {
                    "type": "string", 
                    "description": "The date to check in YYYY-MM-DD format, or natural words like 'today' or 'yesterday'."
                }
            },
            "required": ["date_string"],
        },
    },
    {
        "name": "open_website",
        "description": "Open a website by URL or common nickname (e.g., 'google.com' or 'brightspace').",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL or name of the site to open."}
            },
            "required": ["url"],
        },
    },
    # In dispatcher.py, inside the TOOLS list
    {
        "name": "send_text",
        "description": "Send an SMS message to a specific contact.",
        "risk": "low",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipient_name": {"type": "string", "description": "The name of the person to text."},
                "message": {"type": "string", "description": "The content of the message."}
            },
            "required": ["recipient_name", "message"],
        },
    }
]



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
        if name == "create_directory":
            import os
            path = params.get("path")
            try:
                os.makedirs(path, exist_ok=True)
                return f"I have successfully established the directory at {path}, Sir."
            except Exception as err:
                return f"I couldn't build the directory, Sir: {err}"
            
        # Inside dispatcher.py, inside handle_action()

        if name == "open_website":
            import webbrowser
            url = params.get("url")
            
            # Add your custom shortcuts here
            shortcuts = {
                "brightspace": "https://your-school-url-here.com",
                "portal": "https://another-url.com"
            }
            
            # Check if the user input is a nickname
            target_url = shortcuts.get(url.lower(), url)
            
            if not target_url.startswith("http://") and not target_url.startswith("https://"):
                target_url = "https://" + target_url
                
            try:
                webbrowser.open(target_url)
                return f"Opening {url}, Sir."
            except Exception as err:
                return f"I could not load the webpage, Sir: {err}"

        if name == "delete_directory":
            import shutil
            path = params.get("path")
            try:
                if os.path.exists(path):
                    shutil.rmtree(path)
                    return f"The directory at {path} has been entirely purged, Sir."
                else:
                    return f"I could not locate a directory at {path} to erase, Sir."
            except Exception as err:
                return f"Operation failed, Sir. I couldn't delete the folder: {err}"
        if name == "launch_application":
            import subprocess
            app = params.get("app_name")
            try:
                # Popen ensures Python doesn't freeze waiting for you to close the app
                subprocess.Popen(app, shell=True)
                return f"Launching {app} immediately, Sir."
            except Exception as err:
                return f"I was unable to initialize the application, Sir: {err}"

        if name == "open_website":
            import webbrowser
            url = params.get("url")
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            try:
                webbrowser.open(url)
                return f"Opening your requested terminal link to {url} now, Sir."
            except Exception as err:
                return f"I could not load the webpage, Sir: {err}"
        if name == "get_stock_price":
            return get_stock_summary(params["ticker"]).spoken_summary()

        if name == "get_watchlist":
            summaries = get_portfolio_summary(params["tickers"])
            if not summaries:
                return "I couldn't resolve any of those tickers, Sir."
            return " ".join(s.spoken_summary() for s in summaries)
        # In dispatcher.py, inside handle_action()
        
        if name == "check_emails_by_date":
            import imaplib
            import email
            from email.header import decode_header
            from datetime import datetime, timedelta

            date_str = params.get("date_string", "").lower()
            target_date = None

            if "today" in date_str:
                target_date = datetime.today()
            elif "yesterday" in date_str:
                target_date = datetime.today() - timedelta(days=1)
            else:
                try:
                    target_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                except ValueError:
                    target_date = datetime.today()


            imap_date_format = target_date.strftime("%d-%b-%Y")

            user = os.getenv("JARVIS_EMAIL")
            password = os.getenv("JARVIS_EMAIL_PASSWORD")

            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(user, password)
                mail.select("INBOX", readonly=True) 
                day_after = (target_date + timedelta(days=1)).strftime("%d-%b-%Y")
                search_query = f'(SINCE "{imap_date_format}" BEFORE "{day_after}")'
                
                status, response_data = mail.search(None, search_query)
                if status != "OK":
                    return f"I couldn't complete the query sequence on your inbox, Sir."

                msg_ids = response_data[0].split()
                email_count = len(msg_ids)

                if email_count == 0:
                    return f"Your inbox has no logged transmissions from {target_date.strftime('%B %d, %Y')}, Sir."

                briefing = f"You received {email_count} emails on {target_date.strftime('%B %d, %Y')}, Sir. "

                recent_ids = msg_ids[-3:]
                briefing += "Here are the most notable entries: "
                
                for m_id in reversed(recent_ids):
                    status, msg_data = mail.fetch(m_id, "(RFC822.HEADER)")
                    if status != "OK":
                        continue
                        
                    raw_msg = msg_data[0][1]
                    msg = email.message_from_bytes(raw_msg)
                    
                    # Cleanly extract and decode the Subject / Sender metadata
                    subject, encoding = decode_header(msg.get("Subject", "No Subject"))[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")
                        
                    from_addr = msg.get("From", "Unknown Sender")
                    clean_sender = from_addr.split("<")[0].strip() # Strip out raw angled bracketted addresses
                    
                    briefing += f"A message from {clean_sender} regarding '{subject}'. "

                mail.logout()
                return briefing

            except Exception as err:
                return f"I ran into an issue scanning your primary directory, Sir: {err}"

        if name == "get_weather":
            return get_weather_summary(params["location"]).spoken_summary()
        
        if name == "send_whatsapp":
            return send_whatsapp_message(params["recipient_name"], params["message"])

        if name == "send_email":
            import smtplib
            from email.mime.text import MIMEText

            to_email = params.get("to_email")
            subject = params.get("subject")
            body = params.get("body")
            user = os.getenv("JARVIS_EMAIL")
            password = os.getenv("JARVIS_EMAIL_PASSWORD")
            try:
                msg = MIMEText(body)
                msg["Subject"] = subject
                msg["From"] = sender
                msg["To"] = to_email

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(sender, password)
                    server.sendmail(sender, [to_email], msg.as_string())
                return f"Email transmitted successfully to {to_email}, Sir."
            except Exception as err:
                return f"I ran into an issue dispatching that email, Sir: {err}"

        if name == "get_upcoming_events":
            import datetime
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            max_res = int(params.get("max_results", 5))

            try:

                if not os.path.exists("token.json"):
                    return "I cannot access your calendar, Sir. The authentication token token.json is missing."

                creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/calendar.readonly"])
                service = build("calendar", "v3", credentials=creds)

                now = datetime.datetime.utcnow().isoformat() + "Z"
                events_result = service.events().list(
                    calendarId="primary", timeMin=now,
                    maxResults=max_res, singleEvents=True,
                    orderBy="startTime"
                ).execute()
                events = events_result.get("items", [])

                if not events:
                    return "Your schedule appears completely clear, Sir."

                briefing = "Here are your next upcoming events, Sir: "
                for event in events:
                    start = event["start"].get("dateTime", event["start"].get("date"))
                    # Clean up the ISO timestamp into human-readable spoken time
                    time_str = start.split("T")[0] if "T" not in start else start.split("T")[1][:5]
                    briefing += f"{event['summary']} scheduled at {time_str}. "
                return briefing

            except Exception as err:
                return f"I wasn't able to compile your schedule, Sir: {err}"

        if name == "deep_research":
            topic = params.get("topic") or next(iter(params.values()), None) if params else None
            if not topic:
                return "I couldn't isolate a research topic from that request, Sir."

            num_src = params.get("num_sources")
            if num_src is not None:
                try:
                    if isinstance(num_src, str) and num_src.isdigit():
                        num_src = int(num_src)
                    elif isinstance(num_src, str):
                        from word2number import w2n
                        num_src = w2n.word_to_num(num_src)
                    else:
                        num_src = int(num_src)
                except (ValueError, TypeError):
                    num_src = None  

            report = deep_research(str(topic), num_sources=num_src)
            return report.spoken_summary()
        return f"I don't have a handler for '{name}' yet, Sir."
    
        
    

    except Exception as e:
        return f"I ran into a problem with that request, Sir: {e}"