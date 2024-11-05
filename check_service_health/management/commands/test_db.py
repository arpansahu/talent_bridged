# check_service_health/management/commands/test_db.py

from django.core.management.base import BaseCommand
from check_service_health.models import TestModel

class Command(BaseCommand):
    help = 'Test if the database is working properly'

    def handle(self, *args, **kwargs):
        try:
            # Create a test entry
            test_entry = TestModel.objects.create(name='Test Entry')
            self.stdout.write(self.style.SUCCESS(f'Successfully created test entry: {test_entry}'))

            # Read the test entry
            retrieved_entry = TestModel.objects.get(name='Test Entry')
            self.stdout.write(self.style.SUCCESS(f'Successfully retrieved test entry: {retrieved_entry}'))

            # Update the test entry
            retrieved_entry.name = 'Updated Test Entry'
            retrieved_entry.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated test entry: {retrieved_entry}'))

            # Delete the test entry
            retrieved_entry.delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted test entry'))

            # Confirm deletion
            if not TestModel.objects.filter(name='Updated Test Entry').exists():
                self.stdout.write(self.style.SUCCESS('Database test completed successfully'))
            else:
                self.stdout.write(self.style.ERROR('Test entry was not deleted'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {e}'))