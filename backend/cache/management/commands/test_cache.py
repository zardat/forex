"""
Django management command to test cache service.
Usage: python manage.py test_cache
"""

from django.core.management.base import BaseCommand
from cache.test_cache import run_all_tests


class Command(BaseCommand):
    help = 'Test the cache service functionality'

    def handle(self, *args, **options):
        """Run all cache tests"""
        success = run_all_tests()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('\n✓ All cache tests passed!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n✗ Some cache tests failed. Check output above.')
            )
