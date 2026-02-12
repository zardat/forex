import logging
from celery import shared_task
from django.db import transaction
from django.db.models import Min, Max, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from market.models import ForexPriceSnapshot, ForexCandle, ForexPair, ForexPriceHistory
from market.services.pair_services import PairService
from market.services.price_services import PriceService
from market.providers.forexrateapi import ForexRateAPIProvider
from cache.services import CacheService

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def poll_latest_prices(self):
    """
    Poll latest prices for all active forex pairs using optimized batch processing.
    Uses batch requests and rate inversion to minimize API calls.
    Continues processing other pairs even if some fail.
    """
    # Get list of active pair symbols
    pair_symbols = PairService.list_active_pairs()
    
    if not pair_symbols:
        return {"message": "No active pairs found", "updated": 0}
    
    # Initialize provider and cache service
    provider = ForexRateAPIProvider()
    cache_service = CacheService()
    
    # Fetch all prices in optimized batches (reduces API calls significantly)
    try:
        batch_results = provider.get_latest_prices_batch(pair_symbols)
        logger.info(f"Batch fetch completed: {len(batch_results)}/{len(pair_symbols)} pairs fetched")
    except Exception as e:
        logger.error(f"Batch fetch failed: {e}", exc_info=True)
        batch_results = {}
    
    updated_count = 0
    failed_count = 0
    failed_pairs = []
    
    # Process results from batch fetch
    for symbol in pair_symbols:
        if symbol not in batch_results:
            failed_count += 1
            failed_pairs.append(symbol)
            logger.warning(f"No price data returned for {symbol} from batch fetch")
            continue
        
        try:
            # Get ForexPair object (not just symbol string)
            pair = PairService.get_pair(symbol)
            data = batch_results[symbol]
            
            # Update or create snapshot in database
            with transaction.atomic():
                snapshot, created = ForexPriceSnapshot.objects.update_or_create(
                    pair=pair,
                    defaults={
                        "price": data["price"],
                        "bid": data.get("bid", data["price"]),  # Fallback to price if bid not available
                        "ask": data.get("ask", data["price"]),  # Fallback to price if ask not available
                    }
                )
                
                # Also store in historical table for candle aggregation
                ForexPriceHistory.objects.create(
                    pair=pair,
                    price=data["price"],
                    bid=data.get("bid", data["price"]),
                    ask=data.get("ask", data["price"]),
                    timestamp=timezone.now()
                )
            
            # Update cache using CacheService
            cache_data = PriceService._serialize_snapshot(snapshot)
            cache_service.set_price(symbol, cache_data)
            
            updated_count += 1
            logger.info(f"Successfully updated price for {symbol}")
            
        except Exception as e:
            # Log error but continue with other pairs
            failed_count += 1
            failed_pairs.append(symbol)
            logger.warning(f"Failed to update price for {symbol}: {e}", exc_info=True)
            # Don't retry here - let the task complete for other pairs
            continue
    
    # Calculate unique base currencies (estimate of API calls made)
    unique_bases = set()
    for symbol in pair_symbols:
        try:
            base, _ = provider._parse_symbol(symbol)
            unique_bases.add(base)
        except:
            pass
    
    result = {
        "message": f"Updated {updated_count}/{len(pair_symbols)} pairs",
        "updated": updated_count,
        "failed": failed_count,
        "api_calls_made": len(unique_bases),  # Number of batch API calls made
        "pairs_processed": len(pair_symbols),
    }
    
    if failed_pairs:
        result["failed_pairs"] = failed_pairs
    
    return result


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def aggregate_candles(self, interval: str):
    """
    Aggregate historical price snapshots into OHLC candles for a specific interval.
    
    This task reads from ForexPriceHistory (which stores snapshots every 30 seconds)
    and aggregates them into candles based on the interval.
    
    Supported intervals: '5m', '15m', '1h', '1d'
    
    Args:
        interval: Timeframe interval ('5m', '15m', '1h', '1d')
    
    Returns:
        dict: Summary of candles created
    """
    # Validate interval
    valid_intervals = ['5m', '15m', '1h', '1d']
    if interval not in valid_intervals:
        error_msg = f"Invalid interval: {interval}. Supported: {valid_intervals}"
        logger.error(error_msg)
        return {"error": error_msg, "candles_created": 0}
    
    # Get all active pairs
    pairs = ForexPair.objects.filter(is_active=True)
    
    if not pairs.exists():
        return {"message": "No active pairs found", "candles_created": 0, "interval": interval}
    
    logger.info(f"Aggregating {interval} candles for {pairs.count()} pairs from price history")
    
    candles_created = 0
    candles_updated = 0
    failed_count = 0
    failed_pairs = []
    
    # Calculate time delta for the interval
    interval_deltas = {
        '5m': timedelta(minutes=5),
        '15m': timedelta(minutes=15),
        '1h': timedelta(hours=1),
        '1d': timedelta(days=1),
    }
    interval_delta = interval_deltas[interval]
    
    # Calculate how far back to look for historical data
    # For each interval, we need at least one full period of data
    lookback_time = timezone.now() - interval_delta
    
    for pair in pairs:
        try:
            # Get historical price snapshots for this pair within the lookback period
            # We need enough data to create at least one complete candle
            price_history = ForexPriceHistory.objects.filter(
                pair=pair,
                timestamp__gte=lookback_time
            ).order_by('timestamp')
            
            if not price_history.exists():
                logger.debug(f"No price history found for {pair.symbol} in the last {interval}")
                continue
            
            # Group snapshots by candle period
            candles_data = {}
            
            for snapshot in price_history:
                # Round down timestamp to the start of the candle period
                snapshot_time = snapshot.timestamp
                
                if interval == '5m':
                    candle_start = snapshot_time.replace(
                        minute=(snapshot_time.minute // 5) * 5,
                        second=0,
                        microsecond=0
                    )
                elif interval == '15m':
                    candle_start = snapshot_time.replace(
                        minute=(snapshot_time.minute // 15) * 15,
                        second=0,
                        microsecond=0
                    )
                elif interval == '1h':
                    candle_start = snapshot_time.replace(
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                elif interval == '1d':
                    candle_start = snapshot_time.replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                
                # Initialize candle data if not exists
                if candle_start not in candles_data:
                    candles_data[candle_start] = {
                        'open': snapshot.price,
                        'high': snapshot.price,
                        'low': snapshot.price,
                        'close': snapshot.price,
                        'count': 0,
                    }
                
                # Update OHLC values
                candle = candles_data[candle_start]
                if snapshot.price > candle['high']:
                    candle['high'] = snapshot.price
                if snapshot.price < candle['low']:
                    candle['low'] = snapshot.price
                candle['close'] = snapshot.price  # Close is always the last price in the period
                candle['count'] += 1
            
            # Create or update candles in database
            for candle_start, candle_data in candles_data.items():
                candle, created = ForexCandle.objects.get_or_create(
                    pair=pair,
                    timeframe=interval,
                    timestamp=candle_start,
                    defaults={
                        "open": candle_data['open'],
                        "high": candle_data['high'],
                        "low": candle_data['low'],
                        "close": candle_data['close'],
                        "volume": Decimal('0'),  # Volume not available from snapshots
                    }
                )
                
                if created:
                    candles_created += 1
                else:
                    # Update existing candle with aggregated data
                    ForexCandle.objects.filter(
                        pair=pair,
                        timeframe=interval,
                        timestamp=candle_start
                    ).update(
                        open=candle_data['open'],
                        high=candle_data['high'],
                        low=candle_data['low'],
                        close=candle_data['close'],
                    )
                    candles_updated += 1
            
            logger.debug(
                f"Processed {len(candles_data)} candles for {pair.symbol} ({interval})"
            )
            
        except Exception as e:
            failed_count += 1
            failed_pairs.append(pair.symbol)
            logger.warning(
                f"Failed to aggregate candles for {pair.symbol} ({interval}): {e}",
                exc_info=True
            )
            continue
    
    result = {
        "message": f"Aggregated {interval} candles: {candles_created} created, {candles_updated} updated",
        "interval": interval,
        "pairs_processed": pairs.count(),
        "candles_created": candles_created,
        "candles_updated": candles_updated,
        "failed": failed_count,
    }
    
    if failed_pairs:
        result["failed_pairs"] = failed_pairs
    
    logger.info(
        f"Candle aggregation completed for {interval}: "
        f"{candles_created} created, {candles_updated} updated, {failed_count} failed"
    )
    
    return result

