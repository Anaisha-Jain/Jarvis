import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model
from faster_whisper import WhisperModel
import requests
import io
import wave
import sys
import time
# 🚀 NEW IMPORT: Connects to your local Ollama background server
import ollama
import pyttsx3
from datetime import datetime

openwakeword.utils.download_models()

def speak(text):
    print(f"\n[JARVIS]: {text}")
    # Initialize a quick, offline low-latency audio engine
    engine = pyttsx3.init()
    engine.setProperty('rate', 175) # Set speaking speed
    engine.say(text)
    engine.runAndWait()

    
# 🌦️ SKILL 1: WEATHER DATA
def fetch_weather(city="Toronto"):
    try:
        url = f"https://wttr.in/{city}?format=%l:+%C,+%t+(Feels+like+%f)"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return "I am currently unable to access environmental telemetry data, Ma'am."
    except Exception:
        return "Network layer timeout. Weather data unreachable, Ma'am."

# 🧠 NEW SKILL: LOCAL LLM FALLBACK BRAIN
def ask_local_llm(user_prompt):
    try:
        # 🚀 THE FIX: Grab your laptop's live date and time dynamically
        current_date_str = datetime.now().strftime("%A, %B %d, %Y")
        
        # Inject the live date right into his system context window
        system_instructions = (
            "You are Jarvis, the highly sophisticated, polite, and advanced AI assistant from Iron Man. "
            f"You address the user as 'Ma'am'. Today's exact current date is {current_date_str}. "
            "Keep your responses short, conversational, and highly efficient. "
            "If the user asks for live news, sports, or real-time info that you do not know, reply ONLY with the exact text: [WANTED_SEARCH: query]"
        )
        
        response = ollama.generate(
            model='llama3.2',
            prompt=f"{system_instructions}\nUser: {user_prompt}\nJarvis:"
        )
        result = response['response'].strip()
        
        # 🚀 THE UPGRADED SEARCH TOOL INTERCEPTOR
        if "[wanted_search:" in result.lower():
            search_query = result.split(":")[-1].replace("]", "").strip()
            print(f"[SYSTEM]: Jarvis requested a live web data patch for: '{search_query}'...")
            
            # Fetch the web results
            web_data = requests.get(f"https://html.duckduckgo.com/html/?q={search_query}", timeout=5).text
            
            # THE FIX: Forcefully ground him with the date again right alongside the web data
            fallback_prompt = (
                f"You are Jarvis, the advanced AI assistant. You address the user as 'Ma'am'.\n"
                f"CRITICAL GROUNDING: Today is strictly {current_date_str}.\n"
                f"Use these raw search snippets to answer the user's question concisely:\n"
                f"--- WEB DATA ---\n{web_data[:1200]}\n----------------\n"
                f"User Question: {user_prompt}\n"
                f"Jarvis:"
            )
            
            fallback_response = ollama.generate(
                model='llama3.2',
                prompt=fallback_prompt
            )
            return fallback_response['response'].strip()
            
        return result
    except Exception as e:
        return f"I am having trouble accessing my internal cognitive matrix, Ma'am. Error: {str(e)}"
            

def start_jarvis_engine():
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1280
    
    audio_capture = pyaudio.PyAudio()
    mic_stream = audio_capture.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )
    
    speak("Loading core intelligence models and transcription arrays...")
    wakeword_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    whisper_brain = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    
    speak("Systems online. Ready for your directive, Ma'am.")
    
    while True:
        try:
            raw_audio_frame = mic_stream.read(CHUNK, exception_on_overflow=False)
            numeric_audio = np.frombuffer(raw_audio_frame, dtype=np.int16)
            
            prediction = wakeword_model.predict(numeric_audio)
            
            for model_name, display_scores in wakeword_model.prediction_buffer.items():
                if display_scores[-1] > 0.6:  # TRIGGERED
                    speak("At your service, Ma'am.")
                    
                    print("[SYSTEM]: Recording voice command (4 seconds)...")
                    mic_stream.read(mic_stream.get_read_available(), exception_on_overflow=False) # Flush cache
                    command_frames = []
                    for _ in range(int(RATE / CHUNK * 4)):
                        data = mic_stream.read(CHUNK, exception_on_overflow=False)
                        command_frames.append(data)
                    
                    audio_data = b"".join(command_frames)
                    audio_buffer = io.BytesIO()
                    with wave.open(audio_buffer, "wb") as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(audio_capture.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(audio_data)
                    audio_buffer.seek(0)
                    
                    print("[SYSTEM]: Running local transcription...")
                    segments, info = whisper_brain.transcribe(audio_buffer, beam_size=1)
                    command_text = " ".join([seg.text for seg in segments]).strip().lower()
                    print(f"[YOU SAID]: {command_text}")

                    if "weather" in command_text:
                        speak("Accessing meteorological satellite layers...")
                        
                        # 🚀 THE FIX: Check if you specified a city in your spoken phrase
                        city = "Toronto" # Default fallback
                        if "in " in command_text:
                            # Extracts everything after the word "in " (e.g., "weather in mumbai" -> "mumbai")
                            city = command_text.split("in ")[-1].strip()
                        elif "and " in command_text:
                            # Catching transcription quirks (e.g., "weather and mumbai" -> "mumbai")
                            city = command_text.split("and ")[-1].strip()
                            
                        # Clean up punctuation if the transcriber added a question mark
                        city = city.replace("?", "").title()
                        
                        weather_report = fetch_weather(city)
                        speak(f"For {city}, {weather_report}")
                    elif "power down" in command_text or "exit" in command_text:
                        speak("Shutting down core protocols. Goodbye, Ma'am.")
                        raise KeyboardInterrupt
                    elif command_text == "":
                        speak("I lost your audio signature, Ma'am. Please state your command clearly.")
                    else:
                        # 🚀 THE BRAIN TRIGGER: Anything else goes directly to the LLM!
                        speak("Consulting internal archives...")
                        llm_response = ask_local_llm(command_text)
                        speak(llm_response)
                    
                    # Clear history buffer
                    blank_chunk = np.zeros(CHUNK, dtype=np.int16)
                    for _ in range(25):
                        wakeword_model.predict(blank_chunk)
                        
                    print("\n[SYSTEM]: Loop reset. Awaiting next voice initialization...")
                    
        except KeyboardInterrupt:
            speak("Powering down systems, Ma'am.")
            mic_stream.stop_stream()
            mic_stream.close()
            audio_capture.terminate()
            sys.exit()

if __name__ == "__main__":
    start_jarvis_engine()