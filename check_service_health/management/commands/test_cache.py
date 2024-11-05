# myapp/management/commands/test_cache.py

from django.core.cache import cache
from django.core.management.base import BaseCommand
import time

class Command(BaseCommand):
    help = 'Test if the cache is working properly'

    def handle(self, *args, **kwargs):
        # Set a value in the cache
        cache.set('test_key', 'test_value', timeout=10)  # Cache the value for 10 seconds
        value = cache.get('test_key')
        self.stdout.write(f'Initial cache set: {value}')  # Should output 'test_value'

        if value != 'test_value':
            self.stdout.write(self.style.ERROR('Initial cache set failed'))
            return

        # Wait for 12 seconds to ensure cache expiration
        time.sleep(12)

        # Try to retrieve the value again after the timeout
        value = cache.get('test_key')
        self.stdout.write(f'Value after 12 seconds: {value}')  # Should output None

        if value is None:
            self.stdout.write(self.style.SUCCESS('Cache has expired as expected'))
        else:
            self.stdout.write(self.style.ERROR('Cache is still available: ERROR'))

        # Check if cache is working
        if value == 'test_value':
            self.stdout.write(self.style.ERROR('Cache is not working correctly'))
        else:
            self.stdout.write(self.style.SUCCESS('Cache is working correctly'))