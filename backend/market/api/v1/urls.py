"""
URL configuration for Market API v1.
"""
from django.urls import path
from market.api.v1.views import (
    PairSearchView,
    LatestPriceView,
    BulkPriceView,
    CandleListView,
    TimeframeListView,
)

app_name = 'market_api_v1'

urlpatterns = [
    # Pairs
    path('pairs', PairSearchView.as_view(), name='pair-search'),
    
    # Prices
    path('prices/latest', LatestPriceView.as_view(), name='latest-price'),
    path('prices/latest/bulk', BulkPriceView.as_view(), name='bulk-price'),
    
    # Candles
    path('candles', CandleListView.as_view(), name='candles'),
    
    # Timeframes
    path('timeframes', TimeframeListView.as_view(), name='timeframes'),
]

