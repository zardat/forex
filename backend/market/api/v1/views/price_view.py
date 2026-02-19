"""
Views for price endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request

from market.services.pair_services import PairService
from market.services.price_services import PriceService
from market.providers.forexrateapi import ForexRateAPIProvider
from cache.services import CacheService
from market.api.v1.serializers import (
    LatestPriceSerializer,
    BulkPriceResponseSerializer,
)
from market.api.v1.exceptions import PairNotFoundError, InvalidParameterError


class LatestPriceView(APIView):
    """
    GET /api/v1/market/prices/latest
    
    Get latest price for a single pair.
    Query param: pair (required) - e.g. EURUSD
    """
    def get(self, request: Request):
        pair_symbol = request.query_params.get('pair', '').strip().upper()
        
        if not pair_symbol:
            raise InvalidParameterError("Required parameter 'pair' is missing")
        
        try:
            # Validate pair exists and is active
            PairService.validate_pair(pair_symbol)
        except ValueError as e:
            raise PairNotFoundError(str(e))
        
        # Get price from service layer
        price_service = PriceService(
            provider=ForexRateAPIProvider(),
            cache_service=CacheService()
        )
        
        snapshot_data = price_service.get_latest_price(pair_symbol)
        
        # Convert to API format
        serializer = LatestPriceSerializer(
            data=LatestPriceSerializer.from_snapshot_data(snapshot_data)
        )
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class BulkPriceView(APIView):
    """
    GET /api/v1/market/prices/latest/bulk
    
    Get latest prices for multiple pairs.
    Query param: pairs (required) - comma-separated list, e.g. pairs=EURUSD,USDJPY,GBPUSD
    """
    def get(self, request: Request):
        # Get pairs from query parameters
        pairs_param = request.query_params.get('pairs', '').strip()
        
        if not pairs_param:
            raise InvalidParameterError("Required parameter 'pairs' is missing. Use comma-separated format: ?pairs=EURUSD,USDJPY,GBPUSD")
        
        # Parse comma-separated pairs
        pairs = [p.strip().upper() for p in pairs_param.split(',') if p.strip()]
        
        if not pairs:
            raise InvalidParameterError("No valid pairs provided. Use comma-separated format: ?pairs=EURUSD,USDJPY,GBPUSD")
        
        # Validate pairs count (reasonable limit)
        if len(pairs) > 100:
            raise InvalidParameterError("Maximum 100 pairs allowed per request")
        
        # Normalize and validate all pairs
        price_service = PriceService(
            provider=ForexRateAPIProvider(),
            cache_service=CacheService()
        )
        
        results = {}
        errors = {}
        
        for pair_symbol in pairs:
            normalized = PairService._normalize_symbol(pair_symbol)
            try:
                PairService.validate_pair(normalized)
                snapshot_data = price_service.get_latest_price(normalized)
                
                # Convert to API format
                price_data = LatestPriceSerializer.from_snapshot_data(snapshot_data)
                results[normalized] = {
                    'price': price_data['price'],
                    'timestamp': price_data['timestamp'],
                }
            except ValueError:
                errors[normalized] = "Pair not found or inactive"
        
        # Build response
        response_data = {
            'prices': results
        }
        
        # Include errors if any (optional - could also return 207 Multi-Status)
        if errors:
            response_data['errors'] = errors
        
        serializer = BulkPriceResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

