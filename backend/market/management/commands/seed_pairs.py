# backend/market/management/commands/seed_pairs.py
from django.core.management.base import BaseCommand
from market.models import ForexPair


class Command(BaseCommand):
    help = 'Seed initial forex pairs into the database'

    def handle(self, *args, **options):
        # Common forex pairs
        pairs = [
            {"symbol": "EURUSD", "base": "EUR", "quote": "USD"},
            {"symbol": "GBPUSD", "base": "GBP", "quote": "USD"},
            {"symbol": "USDJPY", "base": "USD", "quote": "JPY"},
            {"symbol": "USDCHF", "base": "USD", "quote": "CHF"},
            {"symbol": "AUDUSD", "base": "AUD", "quote": "USD"},
            {"symbol": "USDCAD", "base": "USD", "quote": "CAD"},
            {"symbol": "NZDUSD", "base": "NZD", "quote": "USD"},
            {"symbol": "EURGBP", "base": "EUR", "quote": "GBP"},
            {"symbol": "EURJPY", "base": "EUR", "quote": "JPY"},
            {"symbol": "GBPJPY", "base": "GBP", "quote": "JPY"},
        ]

        created_count = 0
        for pair_data in pairs:
            pair, created = ForexPair.objects.get_or_create(
                symbol=pair_data["symbol"],
                defaults={
                    "base_currency": pair_data["base"],
                    "quote_currency": pair_data["quote"],
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created {pair_data["symbol"]}')
                )
            else:
                self.stdout.write(
                    f'  {pair_data["symbol"]} already exists'
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Created {created_count} new pairs')
        )