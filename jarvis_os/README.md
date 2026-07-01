# Jarvis - Data Analyst Module

Read-only, low-risk tier of your Jarvis build: stocks, weather, deep research.
No confirmation gateway needed here (that's for the File & App Commander and
Digital Twin modules later) - everything below only *reads* data.

## Setup

```bash
pip install -r requirements.txt

# System deps for the voice pipeline:
#   macOS:   brew install portaudio
#   Ubuntu:  sudo apt-get install portaudio19-dev espeak
#   Windows: sounddevice ships PortAudio in its wheel, nothing extra needed

export ANTHROPIC_API_KEY="sk-ant-..."   # skip if using Ollama (see below)
```

Optional: run everything (research summarization + command routing) through
a local model instead by setting `USE_LOCAL_LLM=true` and pointing at
Ollama — see `config.py`.

## Try it

```bash
python main.py stock AAPL
python main.py watchlist AAPL TSLA MSFT
python main.py weather "Toronto"
python main.py research "solid-state battery breakthroughs 2026"
python main.py listen          # starts the voice pipeline
```

## Voice pipeline

```
IDLE (wake word only) --"hey Jarvis"--> ACTIVE (listening + executing)
   ^                                              |
   |__________________"go to sleep" etc___________|
```

- **Activation**: say **"hey Jarvis"**. This uses openWakeWord's pretrained
  `hey_jarvis` model — always listening, cheap enough to run continuously,
  first run auto-downloads the model weights (~few MB).
- **While active**: every utterance is transcribed with `faster-whisper`
  (runs locally, no API key) and routed through `orchestrator.py`, which
  picks the right tool and executes it.
- **Deactivation**: say any phrase in `config.DEACTIVATION_PHRASES`
  ("go to sleep", "stop listening", "that's all", "jarvis stop", etc.) —
  edit that list to match how you actually talk.
- Utterance end-of-speech is detected by a simple volume (RMS) threshold —
  `config.SILENCE_RMS_THRESHOLD` will need tuning to your mic and room.
  If Jarvis cuts you off mid-sentence, raise `SILENCE_DURATION_S`. If it
  takes too long to respond after you stop talking, lower it.
- Set `config.TTS_ENABLED = False` to run text-only (useful over SSH /
  without speakers, or while tuning thresholds and watching the console).

## Files

| File | Purpose |
|---|---|
| `stocks.py` | Live quotes via `yfinance` (no API key needed) |
| `weather.py` | Current conditions via Open-Meteo (free, no API key) |
| `research.py` | Search (DuckDuckGo) → fetch & clean (`trafilatura`) → summarize (Anthropic or local LLM) |
| `dispatcher.py` | `TOOLS` schema + `handle_action()` — executes a structured action |
| `orchestrator.py` | Transcript → tool call, via Anthropic or Ollama function-calling |
| `voice.py` | Wake word + STT state machine (IDLE/ACTIVE), TTS output |
| `config.py` | All settings, read from env vars |
| `main.py` | CLI — test individual tools, or run `listen` for full voice mode |

## Wiring this into the rest of Jarvis

This module is now a complete, closed loop end to end: wake word →
transcribe → orchestrator picks a tool → `dispatcher.handle_action()`
executes it → speaks the result. When you build the File & App Commander
or Digital Twin modules:

1. Add their tool definitions to `dispatcher.TOOLS` (with a `"risk"` field —
   this module's tools are all `"low"`).
2. Add their handlers to `dispatcher.handle_action()`.
3. In `dispatcher.handle_action()`, before executing anything tagged
   `"risk": "high"`, return a confirmation prompt instead of the result,
   and hold a `PENDING_CONFIRMATION` state until `voice.py` hears a
   confident "proceed" / "do it". That gate belongs in the dispatcher, not
   voice.py, so it protects every entry point (voice, text, cron) equally.

## Notes / things to watch

- **yfinance** is unofficial and occasionally gets rate-limited or breaks when
  Yahoo changes their backend. Fine for personal use; don't rely on it for
  anything that needs guaranteed uptime. Alpha Vantage or Polygon.io are
  paid fallbacks if it gets flaky.
- **ddgs (DuckDuckGo search)** has no official API and can rate-limit under
  heavy use. For a production-grade research agent, consider a real search
  API (Brave Search API, Tavily, or Exa) — swap-in point is `research._search()`.
- **trafilatura** will fail silently (returns `None`) on JS-heavy or paywalled
  sites — that's why `deep_research()` over-fetches (`num_sources * 2`) and
  skips failures rather than erroring out.
- All three tools here are "risk: low" in the schema. When you build the next
  module, copy this file's shape but add a confirmation step in the
  dispatcher for anything tagged "risk: high" before calling the handler.
