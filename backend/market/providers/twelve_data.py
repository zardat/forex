import os
import requests
import time
from decimal import Decimal
from typing import List, Dict

from .base import MarketDataProvider
from datetime import datetime, timezone

class TwelveDataProvider(MarketDataProvider):

    BASE_URL = "https://api.twelvedata.com"

    INTERVAL_MAP = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "1h": "1h",
        "1d": "1day",
    }

    def __init__(self):
        self.api_key = os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key:
            raise RuntimeError("TWELVE_DATA_API_KEY not set")

    @staticmethod
    def _denormalize_symbol(symbol: str) -> str:
        """
        Convert normalized symbol (EURUSD) to API format (EUR/USD).
        Assumes 6-character pairs (3 base + 3 quote).
        If symbol already has '/', returns as-is.
        """
        if "/" in symbol:
            return symbol.upper()
        
        if len(symbol) == 6:
            return f"{symbol[:3]}/{symbol[3:]}"
        
        # Fallback: return as-is if format is unexpected
        return symbol.upper()

    def get_latest_price(self, symbol: str) -> Dict:
        """
        Fetch latest price for a forex pair.
        Converts normalized symbol (EURUSD) to API format (EUR/USD).
        """
        # Convert normalized symbol to API format
        api_symbol = self._denormalize_symbol(symbol)

        url = f"{self.BASE_URL}/price"
        params = {
            "symbol": api_symbol,
            "apikey": self.api_key
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        # Error handling (Twelve Data style)
        if response.status_code != 200 or "price" not in data:
            raise RuntimeError(
                f"TwelveData error for {api_symbol} (normalized: {symbol}): {data}"
            )

        price = Decimal(data["price"])
        
        # TwelveData price endpoint doesn't provide bid/ask separately
        # Use the same price for both (or extract from data if available)
        bid = Decimal(data.get("bid", data["price"]))
        ask = Decimal(data.get("ask", data["price"]))
        
        return {
            "symbol": symbol,  # Return normalized symbol for consistency
            "price": price,
            "bid": bid,
            "ask": ask,
            "timestamp": int(time.time()),  # UTC epoch
            "provider": "twelve_data"
        }

    def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch OHLC candles for a forex pair.
        Converts normalized symbol (EURUSD) to API format (EUR/USD).
        """
        if interval not in self.INTERVAL_MAP:
            raise ValueError(f"Unsupported interval: {interval}")

        # Convert normalized symbol to API format
        api_symbol = self._denormalize_symbol(symbol)

        url = f"{self.BASE_URL}/time_series"
        params = {
            "symbol": api_symbol,
            "interval": self.INTERVAL_MAP[interval],
            "outputsize": limit,
            "order": "ASC",
            "apikey": self.api_key,
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200 or "values" not in data:
            raise RuntimeError(
                f"TwelveData candle error for {api_symbol} (normalized: {symbol}): {data}"
            )

        candles = []

        for item in data["values"]:
            dt = datetime.strptime(
                item["datetime"],
                "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=timezone.utc)

            candles.append({
                "timestamp": int(dt.timestamp()),
                "open": Decimal(item["open"]),
                "high": Decimal(item["high"]),
                "low": Decimal(item["low"]),
                "close": Decimal(item["close"]),
                "volume": None,
            })

        return candles
