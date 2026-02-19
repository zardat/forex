"""
Serializers for forex pair endpoints.
"""
from rest_framework import serializers
from market.models import ForexPair


class PairSerializer(serializers.ModelSerializer):
    """
    Serializer for forex pair search results.
    Converts model fields to API contract format.
    """
    id = serializers.IntegerField(read_only=True)
    symbol = serializers.CharField(read_only=True)
    base = serializers.CharField(source='base_currency', read_only=True)
    quote = serializers.CharField(source='quote_currency', read_only=True)

    class Meta:
        model = ForexPair
        fields = ['id', 'symbol', 'base', 'quote']
        read_only_fields = ['id', 'symbol', 'base', 'quote']


class PairListResponseSerializer(serializers.Serializer):
    """
    Response wrapper for pair list endpoint.
    """
    pairs = PairSerializer(many=True)

