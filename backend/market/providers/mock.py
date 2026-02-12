from decimal import Decimal
from typing import List, Dict
from .base import MarketDataProvider
import time


class MockMarketDataProvider(MarketDataProvider):

    def get_latest_price(self, symbol: str) -> Dict:
        return {
            "symbol": symbol,
            "price": Decimal("1.2345"),
            "timestamp": int(time.time()),
            "provider": "mock"
        }

    def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 10
    ) -> List[Dict]:

        now = int(time.time())
        candles = []

        for i in range(limit):
            candles.append({
                "timestamp": now - i * 60,
                "open": Decimal("1.2300"),
                "high": Decimal("1.2350"),
                "low": Decimal("1.2280"),
                "close": Decimal("1.2345"),
                "volume": None
            })

        return candles
