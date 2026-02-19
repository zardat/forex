"""
URL configuration for market app.
Includes versioned API routes.
"""
from django.urls import path, include
from market.views import api_test_page

app_name = 'market'

urlpatterns = [
    # API test page
    path('api-test/', api_test_page, name='api-test'),
    # API v1
    path('api/v1/market/', include('market.api.v1.urls')),
]

