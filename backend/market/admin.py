from django.contrib import admin
from .models import (
    ForexPair,
    ForexCandle,
    ForexPriceSnapshot,
    ForexPriceHistory,
)


@admin.register(ForexPair)
class ForexPairAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'base_currency', 'quote_currency', 'is_active', 'created_at']
    list_filter = ['is_active', 'base_currency', 'quote_currency', 'created_at']
    search_fields = ['symbol', 'base_currency', 'quote_currency']
    readonly_fields = ['created_at']
    list_editable = ['is_active']


@admin.register(ForexCandle)
class ForexCandleAdmin(admin.ModelAdmin):
    list_display = ['pair', 'timeframe', 'open', 'high', 'low', 'close', 'volume', 'timestamp']
    list_filter = ['timeframe', 'timestamp', 'pair']
    search_fields = ['pair__symbol']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(ForexPriceSnapshot)
class ForexPriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ['pair', 'price', 'bid', 'ask', 'timestamp']
    list_filter = ['timestamp', 'pair']
    search_fields = ['pair__symbol']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(ForexPriceHistory)
class ForexPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['pair', 'price', 'bid', 'ask', 'timestamp']
    list_filter = ['timestamp', 'pair']
    search_fields = ['pair__symbol']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
