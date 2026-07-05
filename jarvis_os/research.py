from dataclasses import dataclass, field

import requests
import trafilatura
from ddgs import DDGS

import config as config


@dataclass
class Source:
    title: str
    url: str
    text: str 

@dataclass
class ResearchReport:
    topic: str
    summary: str
    sources: list[Source] = field(default_factory=list)

    def spoken_summary(self) -> str:
        return self.summary


def _search(topic: str, count: int) -> list[dict]:
    with DDGS() as ddgs:
        results = list(ddgs.text(topic, max_results=count))
    return results


def _fetch_clean_text(url: str) -> str | None:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        text = trafilatura.extract(downloaded)
        if not text:
            return None
        return text[: config.MAX_CHARS_PER_SOURCE]
    except Exception:
        return None


def _summarize_with_ollama(topic: str, sources: list[Source]) -> str:
    context_blocks = "\n\n".join(
        f"SOURCE: {s.title} ({s.url})\n{s.text}" for s in sources
    )
    prompt = (
        f"Summarize the following sources into a concise, spoken-friendly briefing "
        f"on: '{topic}'. 4-6 sentences, plain language, no markdown.\n\n{context_blocks}"
    )
    resp = requests.post(
        f"{config.OLLAMA_HOST}/api/generate",
        json={"model": config.OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def deep_research(topic: str, num_sources: int = None) -> ResearchReport:
    """
    Full pipeline: search -> fetch -> clean -> summarize.
    This is the function your dispatcher calls for "Jarvis, research X".
    """
    num_sources = num_sources or config.RESEARCH_SOURCE_COUNT

    raw_results = _search(topic, num_sources * 2)  # over-fetch, some will fail to parse
    sources: list[Source] = []

    for r in raw_results:
        if len(sources) >= num_sources:
            break
        url = r.get("href") or r.get("url")
        title = r.get("title", url)
        if not url:
            continue
        text = _fetch_clean_text(url)
        if text:
            sources.append(Source(title=title, url=url, text=text))

    if not sources:
        return ResearchReport(
            topic=topic,
            summary="I couldn't pull readable content from any sources on that topic, Sir.",
            sources=[],
        )

    summary = _summarize_with_ollama(topic, sources)
    return ResearchReport(topic=topic, summary=summary, sources=sources)