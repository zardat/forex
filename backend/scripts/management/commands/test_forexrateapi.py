"""
Django management command to test ForexRateAPI provider.
Usage: python manage.py test_forexrateapi
"""

from django.core.management.base import BaseCommand
from scripts.test_forexrateapi import run_all_tests


class Command(BaseCommand):
    help = 'Test the ForexRateAPI provider functionality'

    def handle(self, *args, **options):
        """Run all ForexRateAPI provider tests"""
        success = run_all_tests()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('\n✓ All ForexRateAPI provider tests passed!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n✗ Some tests failed. Check output above.')
            )
