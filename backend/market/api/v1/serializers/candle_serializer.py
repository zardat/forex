"""
Serializers for candle endpoints.
"""
from rest_framework import serializers
from decimal import Decimal
from market.models import ForexCandle


class CandleSerializer(serializers.ModelSerializer):
    """
    Serializer for individual candle data.
    Converts Decimal fields to float and ensures ISO timestamp.
    """
    timestamp = serializers.DateTimeField(format='iso-8601')
    open = serializers.FloatField()
    high = serializers.FloatField()
    low = serializers.FloatField()
    close = serializers.FloatField()
    volume = serializers.FloatField()

    class Meta:
        model = ForexCandle
        fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        read_only_fields = fields

    def to_representation(self, instance):
        """
        Override to convert Decimal to float.
        """
        data = super().to_representation(instance)
        # Convert Decimal fields to float
        for field in ['open', 'high', 'low', 'close', 'volume']:
            if field in data and isinstance(data[field], (str, Decimal)):
                data[field] = float(Decimal(str(data[field])))
        return data


class CandleListResponseSerializer(serializers.Serializer):
    """
    Response wrapper for candle list endpoint.
    """
    pair = serializers.CharField()
    timeframe = serializers.CharField()
    candles = CandleSerializer(many=True)

