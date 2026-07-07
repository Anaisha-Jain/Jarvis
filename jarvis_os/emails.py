import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("JARVIS_EMAIL")
EMAIL_PASSWORD = os.getenv("JARVIS_EMAIL_PASSWORD")

def send_email(to_email: str, subject: str, body: str) -> str:
    """Sends an email using SMTP."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "My email credentials are not properly configured in the environment variables, Sir."

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Standard Gmail SMTP settings
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return f"Email successfully sent to {to_email}, Sir."
    except Exception as e:
        return f"I encountered an error while trying to send the email, Sir: {e}"

def check_emails_by_date(date_string: str) -> str:
    """Checks the inbox for emails on a specific date (Format: DD-Mon-YYYY)."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "My email credentials are not configured, Sir."

    try:
        # Standard Gmail IMAP settings
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")

        # Search for emails on the given date
        status, messages = mail.search(None, f'(ON "{date_string}")')
        
        if status != "OK":
            return "I had trouble searching your inbox, Sir."

        email_ids = messages[0].split()
        if not email_ids:
            return f"You have no new emails for {date_string}, Sir."

        summary = f"You have {len(email_ids)} emails from that date. "
        
        # Read the latest 3 to avoid overwhelming the voice response
        limit = min(3, len(email_ids))
        for i in range(limit):
            latest_email_id = email_ids[-(i+1)]
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    sender = msg.get("From").split('<')[0].strip()
                    summary += f"One from {sender} regarding {subject}. "

        mail.logout()
        return summary + (" I can read more if you need." if len(email_ids) > 3 else "")
        
    except Exception as e:
        return f"I encountered an error while checking your inbox, Sir: {e}"