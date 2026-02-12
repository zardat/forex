import os
import requests
import time
import logging
from decimal import Decimal
from typing import List, Dict
from datetime import datetime, timezone, timedelta

from .base import MarketDataProvider

logger = logging.getLogger(__name__)


class ForexRateAPIProvider(MarketDataProvider):
    """
    ForexRateAPI provider implementation.
    Documentation: https://forexrateapi.com/documentation
    """

    BASE_URL = "https://api.forexrateapi.com/v1"

    # ForexRateAPI hourly endpoint supports hourly data
    # For other intervals, we'll need to use timeframe endpoint or aggregate
    INTERVAL_MAP = {
        "1h": "hourly",  # Direct support
        "1d": "daily",   # Can use historical endpoint
        # Note: 1m, 5m, 15m, 4h may require different approach
    }

    def __init__(self):
        self.api_key = os.getenv("FOREX_RATE_API_KEY")
        if not self.api_key:
            raise RuntimeError("FOREX_RATE_API_KEY not set")

    @staticmethod
    def _parse_symbol(symbol: str) -> tuple:
        """
        Parse normalized symbol (EURUSD) into base and quote currencies.
        Returns (base_currency, quote_currency)
        """
        if "/" in symbol:
            parts = symbol.upper().split("/")
            if len(parts) == 2:
                return parts[0], parts[1]
        
        if len(symbol) == 6:
            return symbol[:3].upper(), symbol[3:].upper()
        
        raise ValueError(f"Invalid symbol format: {symbol}")

    def get_latest_price(self, symbol: str) -> Dict:
        """
        Fetch latest price for a forex pair.
        Uses ForexRateAPI /latest endpoint.
        """
        base_currency, quote_currency = self._parse_symbol(symbol)

        url = f"{self.BASE_URL}/latest"
        params = {
            "api_key": self.api_key,
            "base": base_currency,
            "currencies": quote_currency,
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        # Error handling
        if not data.get("success", False):
            error = data.get("error", {})
            error_msg = error.get("info", "Unknown error")
            raise RuntimeError(
                f"ForexRateAPI error for {symbol} ({base_currency}/{quote_currency}): {error_msg}"
            )

        rates = data.get("rates", {})
        if quote_currency not in rates:
            raise RuntimeError(
                f"ForexRateAPI: Quote currency {quote_currency} not found in response for {symbol}"
            )

        price = Decimal(str(rates[quote_currency]))
        
        # ForexRateAPI doesn't provide bid/ask separately in latest endpoint
        # Use the same price for both
        return {
            "symbol": symbol,  # Return normalized symbol for consistency
            "price": price,
            "bid": price,  # Same as price (not provided separately)
            "ask": price,  # Same as price (not provided separately)
            "timestamp": int(time.time()),  # UTC epoch
            "provider": "forexrateapi"
        }

    def get_latest_prices_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Fetch latest prices for multiple symbols in optimized batches.
        Uses batch requests and rate inversion to minimize API calls.
        
        Strategy:
        1. Group pairs by base currency
        2. Fetch multiple quote currencies in single batch request
        3. Use rate inversion to avoid duplicate calls (EUR/USD = 1 / USD/EUR)
        
        Returns: Dict mapping symbol -> price data
        """
        if not symbols:
            return {}
        
        # Parse all symbols
        parsed_pairs = {}
        for symbol in symbols:
            try:
                base, quote = self._parse_symbol(symbol)
                parsed_pairs[symbol] = (base, quote)
            except ValueError as e:
                logger.warning(f"Invalid symbol format {symbol}: {e}")
                continue
        
        if not parsed_pairs:
            return {}
        
        results = {}
        fetched_rates = {}  # Cache for rate inversion: (base, quote) -> rate
        
        # Group pairs by base currency for batch requests
        base_groups = {}
        for symbol, (base, quote) in parsed_pairs.items():
            if base not in base_groups:
                base_groups[base] = []
            base_groups[base].append((symbol, quote))
        
        # Fetch rates in batches (one call per base currency)
        for base_currency, pairs in base_groups.items():
            # Get all unique quote currencies for this base
            quote_currencies = list(set(quote for _, quote in pairs))
            
            # Make batch request: base=EUR, currencies=USD,GBP,JPY
            url = f"{self.BASE_URL}/latest"
            params = {
                "api_key": self.api_key,
                "base": base_currency,
                "currencies": ",".join(quote_currencies),  # Batch: multiple currencies
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if not data.get("success", False):
                    error = data.get("error", {})
                    error_msg = error.get("info", "Unknown error")
                    logger.warning(
                        f"ForexRateAPI batch error for base {base_currency}: {error_msg}"
                    )
                    continue
                
                rates = data.get("rates", {})
                
                # Store results and cache for inversion
                for symbol, quote_currency in pairs:
                    if quote_currency in rates:
                        rate = Decimal(str(rates[quote_currency]))
                        fetched_rates[(base_currency, quote_currency)] = rate
                        
                        results[symbol] = {
                            "symbol": symbol,
                            "price": rate,
                            "bid": rate,
                            "ask": rate,
                            "timestamp": int(time.time()),
                            "provider": "forexrateapi"
                        }
            
            except Exception as e:
                logger.warning(
                    f"Error fetching batch for base {base_currency}: {e}",
                    exc_info=True
                )
                continue
        
        # Handle inverses: if we have EUR/USD, calculate USD/EUR = 1 / (EUR/USD)
        for symbol, (base, quote) in parsed_pairs.items():
            if symbol not in results:
                # Check if we have the inverse pair
                inverse_key = (quote, base)
                if inverse_key in fetched_rates:
                    try:
                        # Calculate inverse: USD/EUR = 1 / (EUR/USD)
                        inverse_rate = self._calculate_inverse_rate(fetched_rates[inverse_key])
                        
                        results[symbol] = {
                            "symbol": symbol,
                            "price": inverse_rate,
                            "bid": inverse_rate,
                            "ask": inverse_rate,
                            "timestamp": int(time.time()),
                            "provider": "forexrateapi"
                        }
                        logger.debug(f"Calculated inverse rate for {symbol} from {quote}/{base}")
                    except (ValueError, ZeroDivisionError) as e:
                        logger.warning(f"Cannot calculate inverse for {symbol}: {e}")
        
        return results

    @staticmethod
    def _calculate_inverse_rate(rate: Decimal) -> Decimal:
        """
        Calculate inverse rate: 1 / rate
        Example: EUR/USD = 1.08, then USD/EUR = 1 / 1.08 = 0.9259
        """
        if rate == 0:
            raise ValueError("Cannot calculate inverse of zero rate")
        return Decimal("1") / rate

    def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch OHLC candles for a forex pair.
        Uses ForexRateAPI /hourly endpoint for hourly data.
        For daily data, uses historical endpoint.
        """
        base_currency, quote_currency = self._parse_symbol(symbol)

        # ForexRateAPI hourly endpoint supports hourly OHLC data
        if interval == "1h":
            return self._get_hourly_candles(base_currency, quote_currency, limit)
        elif interval == "1d":
            return self._get_daily_candles(base_currency, quote_currency, limit)
        else:
            # For other intervals, we'll use hourly and aggregate or return error
            raise ValueError(
                f"ForexRateAPI currently supports '1h' and '1d' intervals. "
                f"Requested: {interval}. "
                f"Consider using hourly data and aggregating client-side."
            )

    def _get_hourly_candles(
        self,
        base_currency: str,
        quote_currency: str,
        limit: int
    ) -> List[Dict]:
        """
        Fetch hourly OHLC candles using /hourly endpoint.
        ForexRateAPI hourly endpoint returns OHLC data for a currency pair.
        """
        # Calculate date range (limit hours back from now)
        end_date = datetime.now(timezone.utc)
        # For hourly, we need to calculate days (max 7 days for free plan, 2 for basic)
        max_days = 2  # Basic plan allows 2 days
        days_back = min(limit // 24 + 1, max_days)  # Add 1 day buffer
        start_date = end_date - timedelta(days=days_back)

        url = f"{self.BASE_URL}/hourly"
        # ForexRateAPI hourly endpoint returns rates for a currency relative to USD
        # For pairs with USD as quote (EUR/USD), request base currency
        # For pairs with USD as base (USD/JPY), request quote currency and invert
        # For cross pairs (GBP/EUR), would need cross-rate calculation (not implemented)
        
        if quote_currency == "USD":
            # USD is quote, so request base currency (e.g., EUR for EUR/USD)
            currency_param = base_currency
        elif base_currency == "USD":
            # USD is base, so request quote currency (e.g., JPY for USD/JPY)
            currency_param = quote_currency
            # Note: Would need to invert rates, but ForexRateAPI returns base/USD format
            # This may need adjustment based on actual API response
        else:
            # Cross pair - would need cross-rate calculation
            raise ValueError(
                f"ForexRateAPI hourly endpoint currently supports USD-quoted pairs only. "
                f"Cross pairs like {base_currency}/{quote_currency} require additional implementation."
            )
        
        params = {
            "api_key": self.api_key,
            "currency": currency_param,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if not data.get("success", False):
            error = data.get("error", {})
            error_msg = error.get("info", "Unknown error")
            raise RuntimeError(
                f"ForexRateAPI hourly error for {base_currency}/{quote_currency}: {error_msg}"
            )

        hourly_data = data.get("hourly", {})
        
        # Log if hourly data is empty or has unexpected structure
        if not hourly_data:
            logger.debug(
                f"ForexRateAPI hourly endpoint returned empty data for {base_currency}/{quote_currency}. "
                f"Response keys: {list(data.keys())}. "
                f"This may indicate the basic plan doesn't support hourly historical data."
            )
        
        candles = []

        # ForexRateAPI returns hourly data in format:
        # {
        #   "2025-11-03": {
        #     "00:00:00": {"open": 1.08, "high": 1.09, "low": 1.07, "close": 1.085},
        #     "01:00:00": {...},
        #     ...
        #   }
        # }
        
        # Collect all candles
        for date_str in sorted(hourly_data.keys(), reverse=True):
            day_data = hourly_data[date_str]
            for time_str, candle_data in day_data.items():
                try:
                    # Parse datetime: "2025-11-03 00:00:00"
                    dt_str = f"{date_str} {time_str}"
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    
                    candles.append({
                        "timestamp": int(dt.timestamp()),
                        "open": Decimal(str(candle_data.get("open", 0))),
                        "high": Decimal(str(candle_data.get("high", 0))),
                        "low": Decimal(str(candle_data.get("low", 0))),
                        "close": Decimal(str(candle_data.get("close", 0))),
                        "volume": None,  # ForexRateAPI doesn't provide volume
                    })
                except (ValueError, KeyError, TypeError):
                    continue  # Skip invalid entries

        # Sort by timestamp descending (newest first) and limit
        candles.sort(key=lambda x: x["timestamp"], reverse=True)
        return candles[:limit]

    def _get_daily_candles(
        self,
        base_currency: str,
        quote_currency: str,
        limit: int
    ) -> List[Dict]:
        """
        Fetch daily candles using historical endpoint.
        Note: ForexRateAPI doesn't provide OHLC for daily, only rates.
        We'll use the rate as close price and estimate OHLC.
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=limit)

        url = f"{self.BASE_URL}/timeframe"
        params = {
            "api_key": self.api_key,
            "base": base_currency,
            "currencies": quote_currency,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if not data.get("success", False):
            error = data.get("error", {})
            error_msg = error.get("info", "Unknown error")
            raise RuntimeError(
                f"ForexRateAPI timeframe error for {base_currency}/{quote_currency}: {error_msg}"
            )

        rates = data.get("rates", {})
        candles = []

        for date_str, day_rates in sorted(rates.items(), reverse=True)[:limit]:
            if quote_currency not in day_rates:
                continue

            rate = Decimal(str(day_rates[quote_currency]))
            
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                
                # ForexRateAPI timeframe only provides close rates, not OHLC
                # Use the rate for all OHLC values
                candles.append({
                    "timestamp": int(dt.timestamp()),
                    "open": rate,
                    "high": rate,
                    "low": rate,
                    "close": rate,
                    "volume": None,
                })
            except (ValueError, KeyError):
                continue

        return candles
