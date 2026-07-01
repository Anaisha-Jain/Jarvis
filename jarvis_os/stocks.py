"""
Jarvis Data Analyst - Stocks

Low-risk / auto-execute tier: read-only market data, nothing destructive.
"""

from dataclasses import dataclass
from typing import Optional

import yfinance as yf


@dataclass
class StockSummary:
    ticker: str
    company_name: str
    price: float
    currency: str
    change: float
    change_pct: float
    day_high: float
    day_low: float
    volume: int
    market_cap: Optional[float]

    def spoken_summary(self) -> str:
        direction = "up" if self.change >= 0 else "down"
        return (
            f"{self.company_name} is trading at {self.price:.2f} {self.currency}, "
            f"{direction} {abs(self.change_pct):.2f} percent today. "
            f"Day range: {self.day_low:.2f} to {self.day_high:.2f}."
        )


def get_stock_summary(ticker: str) -> StockSummary:
    """
    Fetch a live quote summary for a given ticker symbol (e.g. 'AAPL', 'TSLA').
    Raises ValueError if the ticker can't be resolved.
    """
    t = yf.Ticker(ticker.upper())
    info = t.fast_info  # lightweight, avoids full .info scrape when possible

    try:
        price = float(info["lastPrice"])
        prev_close = float(info["previousClose"])
    except Exception as e:
        raise ValueError(f"Could not resolve ticker '{ticker}': {e}")

    change = price - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0.0

    # fast_info doesn't always have the company name; fall back to .info (slower)
    try:
        long_name = t.info.get("longName") or t.info.get("shortName") or ticker.upper()
    except Exception:
        long_name = ticker.upper()

    return StockSummary(
        ticker=ticker.upper(),
        company_name=long_name,
        price=price,
        currency=info.get("currency", "USD"),
        change=change,
        change_pct=change_pct,
        day_high=float(info.get("dayHigh", price)),
        day_low=float(info.get("dayLow", price)),
        volume=int(info.get("lastVolume", 0)),
        market_cap=info.get("marketCap"),
    )


def get_portfolio_summary(tickers: list[str]) -> list[StockSummary]:
    """Batch version for 'give me my watchlist' style requests."""
    results = []
    for tkr in tickers:
        try:
            results.append(get_stock_summary(tkr))
        except ValueError:
            continue  # skip bad tickers rather than failing the whole batch
    return results
