"""
Serializers for price endpoints.
Handles Decimal → float conversion safely.
"""
from rest_framework import serializers
from decimal import Decimal
from typing import Dict, Any


class LatestPriceSerializer(serializers.Serializer):
    """
    Serializer for latest price response.
    Converts Decimal to float and ensures ISO timestamp format.
    """
    pair = serializers.CharField()
    price = serializers.FloatField()
    bid = serializers.FloatField()
    ask = serializers.FloatField()
    timestamp = serializers.DateTimeField(format='iso-8601')

    @staticmethod
    def from_snapshot_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts service layer data (with Decimal strings) to API format.
        Safely converts Decimal strings to floats.
        """
        return {
            'pair': data['symbol'],
            'price': float(Decimal(data['price'])),
            'bid': float(Decimal(data['bid'])),
            'ask': float(Decimal(data['ask'])),
            'timestamp': data['timestamp'],  # Already ISO format from service
        }


class BulkPriceRequestSerializer(serializers.Serializer):
    """
    Request serializer for bulk price endpoint.
    """
    pairs = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=100,  # Reasonable limit
    )


class BulkPriceItemSerializer(serializers.Serializer):
    """
    Single price item in bulk response.
    """
    price = serializers.FloatField()
    timestamp = serializers.DateTimeField(format='iso-8601')


class BulkPriceResponseSerializer(serializers.Serializer):
    """
    Response serializer for bulk price endpoint.
    """
    prices = serializers.DictField(
        child=BulkPriceItemSerializer(),
    )

