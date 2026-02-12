from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class ForexPair(models.Model):
    """Forex currency pair model"""
    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    base_currency = models.CharField(max_length=3, db_index=True)
    quote_currency = models.CharField(max_length=3, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'forex_pair'
        indexes = [
            models.Index(fields=['base_currency', 'quote_currency']),
        ]

    def __str__(self):
        return self.symbol


class ForexCandle(models.Model):
    """OHLCV candle data for forex pairs"""
    TIMEFRAME_CHOICES = [
        ('1m', '1 Minute'),
        ('5m', '5 Minutes'),
        ('15m', '15 Minutes'),
        ('1h', '1 Hour'),
        ('4h', '4 Hours'),
        ('1d', '1 Day'),
    ]

    pair = models.ForeignKey(ForexPair, on_delete=models.CASCADE, related_name='candles')
    timeframe = models.CharField(max_length=3, choices=TIMEFRAME_CHOICES)
    open = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    high = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    low = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    close = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    volume = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'forex_candle'
        unique_together = [['pair', 'timeframe', 'timestamp']]
        indexes = [
            models.Index(fields=['pair', 'timeframe', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.pair.symbol} {self.timeframe} {self.timestamp}"


class ForexPriceSnapshot(models.Model):
    """Current price snapshot for forex pairs"""
    pair = models.OneToOneField(ForexPair, on_delete=models.CASCADE, related_name='price_snapshot')
    price = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    bid = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    ask = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    timestamp = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        db_table = 'forex_price_snapshot'
        indexes = [
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.pair.symbol} @ {self.price}"


class ForexPriceHistory(models.Model):
    """Historical price snapshots for aggregating candles"""
    pair = models.ForeignKey(ForexPair, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    bid = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    ask = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'forex_price_history'
        indexes = [
            models.Index(fields=['pair', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.pair.symbol} @ {self.price} ({self.timestamp})"

