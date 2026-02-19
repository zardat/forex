"""
Views for forex pair endpoints.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from market.models import ForexPair
from market.api.v1.serializers import PairListResponseSerializer


class PairSearchView(APIView):
    """
    GET /api/v1/market/pairs
    
    Search forex pairs by keyword.
    Query param: q (optional) - search keyword (EUR, USD, etc.)
    """
    def get(self, request):
        query = request.query_params.get('q', '').strip().upper()
        
        queryset = ForexPair.objects.filter(is_active=True)
        
        if query:
            # Search by symbol, base_currency, or quote_currency
            queryset = queryset.filter(
                Q(symbol__icontains=query) |
                Q(base_currency__icontains=query) |
                Q(quote_currency__icontains=query)
            )
        
        pairs = queryset.order_by('symbol')[:50]  # Reasonable limit
        
        serializer = PairListResponseSerializer({
            'pairs': pairs
        })
        
        return Response(serializer.data, status=status.HTTP_200_OK)

