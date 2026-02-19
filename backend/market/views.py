"""
Views for market app.
"""
from django.shortcuts import render


def api_test_page(request):
    """
    Test page for API endpoints.
    """
    return render(request, 'market/api_test.html')
