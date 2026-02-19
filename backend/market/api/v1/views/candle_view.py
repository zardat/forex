"""
Views for candle endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime

from market.models import ForexCandle
from market.services.pair_services import PairService
from market.api.v1.serializers import CandleListResponseSerializer
from market.api.v1.exceptions import (
    PairNotFoundError,
    InvalidTimeframeError,
    InvalidParameterError,
)


class CandleListView(APIView):
    """
    GET /api/v1/market/candles
    
    Get historical candles for a pair and timeframe.
    Query params:
    - pair (required) - e.g. EURUSD
    - timeframe (required) - e.g. 1m, 5m, 1h, 1d
    - limit (optional) - number of candles (default: 100, max: 1000)
    - from (optional) - ISO timestamp to start from
    """
    MAX_LIMIT = 1000
    DEFAULT_LIMIT = 100
    
    def get(self, request):
        # Validate required parameters
        pair_symbol = request.query_params.get('pair', '').strip().upper()
        timeframe = request.query_params.get('timeframe', '').strip().lower()
        
        if not pair_symbol:
            raise InvalidParameterError("Required parameter 'pair' is missing")
        if not timeframe:
            raise InvalidParameterError("Required parameter 'timeframe' is missing")
        
        # Validate pair
        try:
            pair = PairService.get_pair(pair_symbol)
        except ValueError as e:
            raise PairNotFoundError(str(e))
        
        # Validate timeframe
        valid_timeframes = [choice[0] for choice in ForexCandle.TIMEFRAME_CHOICES]
        if timeframe not in valid_timeframes:
            raise InvalidTimeframeError(
                f"Invalid timeframe '{timeframe}'. Valid options: {', '.join(valid_timeframes)}"
            )
        
        # Parse optional parameters
        limit = int(request.query_params.get('limit', self.DEFAULT_LIMIT))
        limit = min(limit, self.MAX_LIMIT)  # Enforce max limit
        
        from_timestamp = None
        if 'from' in request.query_params:
            try:
                from_timestamp = datetime.fromisoformat(
                    request.query_params['from'].replace('Z', '+00:00')
                )
                if timezone.is_naive(from_timestamp):
                    from_timestamp = timezone.make_aware(from_timestamp)
            except ValueError:
                raise InvalidParameterError("Invalid 'from' timestamp format. Use ISO 8601.")
        
        # Query candles
        queryset = ForexCandle.objects.filter(
            pair=pair,
            timeframe=timeframe
        ).order_by('-timestamp')
        
        if from_timestamp:
            queryset = queryset.filter(timestamp__lte=from_timestamp)
        
        candles = queryset[:limit]
        
        # Reverse to chronological order (oldest first)
        candles = list(reversed(candles))
        
        # Serialize response
        serializer = CandleListResponseSerializer({
            'pair': pair_symbol,
            'timeframe': timeframe,
            'candles': candles,
        })
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class TimeframeListView(APIView):
    """
    GET /api/v1/market/timeframes
    
    Get list of supported timeframes.
    """
    def get(self, request):
        timeframes = [choice[0] for choice in ForexCandle.TIMEFRAME_CHOICES]
        
        return Response(
            {'timeframes': timeframes},
            status=status.HTTP_200_OK
        )

