import pycountry
from django.core.management.base import BaseCommand
from account.models import Country 

class Command(BaseCommand):
    help = "Populate Country table with country names and codes from pycountry"

    def handle(self, *args, **kwargs):
        # Clear existing data to avoid duplicates
        Country.objects.all().delete()

        # Populate with country data from pycountry
        countries = []
        for country in pycountry.countries:
            countries.append(Country(name=country.name, code=country.alpha_2))
        
        # Bulk create countries
        Country.objects.bulk_create(countries)

        self.stdout.write(self.style.SUCCESS("Successfully populated Country table."))
