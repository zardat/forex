from typing import List

from market.models import ForexPair


class PairService:
    """
    Domain service for forex pairs.
    """

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """
        Normalizes symbol format: converts "EUR/USD" to "EURUSD".
        """
        return symbol.replace("/", "").upper()

    @staticmethod
    def validate_pair(symbol: str) -> None:
        """
        Raises ValueError if pair does not exist or is inactive.
        """
        normalized_symbol = PairService._normalize_symbol(symbol)
        try:
            pair = ForexPair.objects.get(symbol=normalized_symbol)
        except ForexPair.DoesNotExist:
            raise ValueError(f"Invalid forex pair: {symbol}")

        if not pair.is_active:
            raise ValueError(f"Forex pair inactive: {symbol}")

    @staticmethod
    def get_pair(symbol: str) -> ForexPair:
        """
        Returns ForexPair instance or raises error.
        """
        normalized_symbol = PairService._normalize_symbol(symbol)
        try:
            pair = ForexPair.objects.get(symbol=normalized_symbol, is_active=True)
        except ForexPair.DoesNotExist:
            raise ValueError(f"Forex pair not found or inactive: {symbol}")

        return pair

    @staticmethod
    def list_active_pairs() -> List[str]:
        """
        Returns list of active forex pair symbols.
        """
        return list(
            ForexPair.objects
            .filter(is_active=True)
            .values_list("symbol", flat=True)
        )

    @staticmethod
    def is_pair_active(symbol: str) -> bool:
        """
        Checks if a forex pair exists and is active.
        """
        normalized_symbol = PairService._normalize_symbol(symbol)
        return ForexPair.objects.filter(
            symbol=normalized_symbol,
            is_active=True
        ).exists()
