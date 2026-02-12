import json
import logging
from typing import Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CacheService:
    PRICE_TTL = 30
    PAIRS_TTL = 3600

    def __init__(self):
        self.cache = cache

    # ---------- Price ----------
    def get_price(self, pair_symbol: str) -> Optional[dict]:
        """
        Get cached price data for a forex pair.
        Returns None if not found or on error.
        """
        key = f"forex:price:{pair_symbol}"
        try:
            value = self.cache.get(key)
            if value is None:
                return None
            
            # Handle both string and already-deserialized values
            if isinstance(value, str):
                return json.loads(value)
            elif isinstance(value, dict):
                return value
            else:
                logger.warning(f"Unexpected cache value type for {key}: {type(value)}")
                return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to decode JSON for price {pair_symbol}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.warning(f"Redis GET price failed for {pair_symbol}", exc_info=True)
            return None

    def set_price(self, pair_symbol: str, data: dict) -> None:
        """
        Cache price data for a forex pair.
        """
        key = f"forex:price:{pair_symbol}"
        try:
            # Serialize to JSON string for consistent storage
            serialized = json.dumps(data)
            self.cache.set(key, serialized, timeout=self.PRICE_TTL)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize price data for {pair_symbol}: {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"Redis SET price failed for {pair_symbol}", exc_info=True)

    # ---------- Pairs ----------
    def get_active_pairs(self) -> Optional[list]:
        """
        Get cached list of active forex pairs.
        Returns None if not found or on error.
        """
        key = "forex:pairs:active"
        try:
            value = self.cache.get(key)
            if value is None:
                return None
            
            # Handle both string and already-deserialized values
            if isinstance(value, str):
                return json.loads(value)
            elif isinstance(value, list):
                return value
            else:
                logger.warning(f"Unexpected cache value type for {key}: {type(value)}")
                return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to decode JSON for active pairs: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.warning("Redis GET pairs failed", exc_info=True)
            return None

    def set_active_pairs(self, data: list) -> None:
        """
        Cache list of active forex pairs.
        """
        key = "forex:pairs:active"
        try:
            # Serialize to JSON string for consistent storage
            serialized = json.dumps(data)
            self.cache.set(key, serialized, timeout=self.PAIRS_TTL)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize active pairs data: {e}", exc_info=True)
        except Exception as e:
            logger.warning("Redis SET pairs failed", exc_info=True)
