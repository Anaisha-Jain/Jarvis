import pywhatkit
import pyautogui
import time

def send_whatsapp_message(recipient_name: str, message: str) -> str:
    phone_book = {"mom": "+14163719122", "dad": "+14168329485"}
    number = phone_book.get(recipient_name.lower())
    
    try:
        # 1. Open browser and wait for page to load
        pywhatkit.sendwhatmsg_instantly(number, message, wait_time=15, tab_close=False)
        time.sleep(10) # Wait for page to fully load
        
        # 2. Force focus on the browser (this assumes Chrome is open)
        # You can manually click the browser window once it opens to test this.
        
        # 3. Use coordinates to click the send button
        # Adjust these X,Y coordinates to where the green button appears on your screen
        pyautogui.click(x=1850, y=970) 
        
        return f"Message sent to {recipient_name}, Sir."
    except Exception as e:
        return f"Error: {e}"