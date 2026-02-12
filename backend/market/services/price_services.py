from typing import Dict
from django.db import transaction

from market.models import ForexPriceSnapshot
from market.services.pair_services import PairService
from market.providers.base import MarketDataProvider
from cache.services import CacheService


class PriceService:
    """
    Service for fetching latest forex prices.
    """

    def __init__(
        self,
        provider: MarketDataProvider,
        cache_service: CacheService
    ):
        self.provider = provider
        self.cache = cache_service

    def get_latest_price(self, symbol: str) -> Dict:
        # 1. Validate pair
        pair = PairService.get_pair(symbol)

        # 2. Cache lookup (Redis)
        cached = self.cache.get_price(symbol)
        if cached:
            return cached

        # 3. DB fallback
        snapshot = (
            ForexPriceSnapshot.objects
            .filter(pair=pair)
            .first()
        )

        if snapshot:
            data = self._serialize_snapshot(snapshot)
            self.cache.set_price(symbol, data)
            return data

        # 4. Provider fetch
        provider_data = self.provider.get_latest_price(symbol)

        # 5. Normalize + persist
        with transaction.atomic():
            snapshot, _ = ForexPriceSnapshot.objects.update_or_create(
                pair=pair,
                defaults={
                    "price": provider_data["price"],
                    "bid": provider_data.get("bid", provider_data["price"]),  # Fallback to price if bid not available
                    "ask": provider_data.get("ask", provider_data["price"]),  # Fallback to price if ask not available
                }
            )

        # 6. Cache provider result
        data = self._serialize_snapshot(snapshot)
        self.cache.set_price(symbol, data)

        return data

    @staticmethod
    def _serialize_snapshot(snapshot: ForexPriceSnapshot) -> Dict:
        return {
            "symbol": snapshot.pair.symbol,
            "price": str(snapshot.price),
            "bid": str(snapshot.bid),
            "ask": str(snapshot.ask),
            "timestamp": snapshot.timestamp.isoformat(),
        }
