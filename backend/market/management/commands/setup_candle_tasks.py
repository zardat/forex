"""
Django management command to set up periodic candle aggregation tasks.
Usage: python manage.py setup_candle_tasks
"""

import json
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule


class Command(BaseCommand):
    help = 'Set up periodic tasks for aggregating candles from price snapshots'

    def handle(self, *args, **options):
        """Create or update periodic tasks for candle aggregation"""
        
        # Define intervals: (interval_name, every_seconds, description)
        candle_intervals = [
            ('5m', 300, '5 minutes'),      # Every 5 minutes
            ('15m', 900, '15 minutes'),     # Every 15 minutes
            ('1h', 3600, '1 hour'),         # Every 1 hour
            ('1d', 86400, '1 day'),         # Every 1 day
        ]
        
        created_count = 0
        updated_count = 0
        
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
                'Periodic tasks are now scheduled. Make sure Celery Beat is running!'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\nTo start Celery Beat: celery -A core beat -l info'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                '\nNote: Price snapshots are stored in ForexPriceHistory when poll_latest_prices runs.'
            )
        )
