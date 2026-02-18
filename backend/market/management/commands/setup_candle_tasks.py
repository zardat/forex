"""
Django management command to set up periodic tasks for price polling and candle aggregation.
Usage: python manage.py setup_candle_tasks
"""

import json
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule


class Command(BaseCommand):
    help = 'Set up periodic tasks for price polling and aggregating candles from price snapshots'

    def handle(self, *args, **options):
        """Create or update periodic tasks for price polling and candle aggregation"""
        
        created_count = 0
        updated_count = 0
        
        # First, set up the price polling task (runs every 30 seconds)
        self.stdout.write(self.style.SUCCESS('\n=== Setting up Price Polling Task ==='))
        price_schedule, price_schedule_created = IntervalSchedule.objects.get_or_create(
            every=30,
            period=IntervalSchedule.SECONDS,
        )
        
        if price_schedule_created:
            self.stdout.write(
                self.style.SUCCESS('Created interval schedule: 30 seconds')
            )
        
        price_task, price_task_created = PeriodicTask.objects.update_or_create(
            name="Poll latest prices",
            defaults={
                "interval": price_schedule,
                "task": "market.tasks.poll_latest_prices",
                "args": json.dumps([]),
                "enabled": True,
                "description": "Poll latest prices for all active forex pairs every 30 seconds",
            }
        )
        
        if price_task_created:
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS('✓ Created periodic task: Poll latest prices')
            )
        else:
            updated_count += 1
            self.stdout.write(
                self.style.WARNING('↻ Updated periodic task: Poll latest prices')
            )
        
        # Then, set up candle aggregation tasks
        self.stdout.write(self.style.SUCCESS('\n=== Setting up Candle Aggregation Tasks ==='))
        
        # Define intervals: (interval_name, every_seconds, description)
        candle_intervals = [
            ('5m', 300, '5 minutes'),      # Every 5 minutes
            ('15m', 900, '15 minutes'),     # Every 15 minutes
            ('1h', 3600, '1 hour'),         # Every 1 hour
            ('1d', 86400, '1 day'),         # Every 1 day
        ]
        
        for interval_name, every_seconds, description in candle_intervals:
            # Create or get interval schedule
            schedule, schedule_created = IntervalSchedule.objects.get_or_create(
                every=every_seconds,
                period=IntervalSchedule.SECONDS,
            )
            
            if schedule_created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created interval schedule: {description} ({every_seconds}s)')
                )
            
            # Create or update periodic task
            task_name = f"Aggregate {interval_name} candles"
            task, task_created = PeriodicTask.objects.update_or_create(
                name=task_name,
                defaults={
                    "interval": schedule,
                    "task": "market.tasks.aggregate_candles",
                    "args": json.dumps([interval_name]),  # Pass interval as argument
                    "enabled": True,
                    "description": f"Aggregate candle data from price snapshots at {description} interval",
                }
            )
            
            if task_created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created periodic task: {task_name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated periodic task: {task_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Setup complete: {created_count} created, {updated_count} updated'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                '\nAll periodic tasks are now scheduled:'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                '  • Price polling: every 30 seconds'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                '  • Candle aggregation: 5m, 15m, 1h, 1d intervals'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\n⚠ Make sure Celery Beat is running!'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                'To start Celery Beat: celery -A core beat -l info'
            )
        )
