from abc import ABC, abstractmethod
from typing import List, Dict
from decimal import Decimal

class MarketDataProvider(ABC):
    """
    Base contract for all market data providers.
    """

    @abstractmethod
    def get_latest_price(self, symbol: str) -> Dict:
        """
        Returns latest price for a symbol.
        """
        pass

    @abstractmethod
    def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Returns OHLC candles.
        """
        pass

# for normalization
candle_format = {
    "timestamp": 1707475200,
    "open": Decimal("1.0820"),
    "high": Decimal("1.0850"),
    "low": Decimal("1.0810"),
    "close": Decimal("1.0842"),
    "volume": None
}
