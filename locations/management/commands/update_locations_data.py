from django.core.management.base import BaseCommand, CommandError
from locations.models import Locations
from django.conf import settings
import pandas as pd


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("---------------------Update Locations Command Started----------------------")
        csv_path = os.path.join(os.path.dirname(__file__), 'world_cities.csv')
        df = pd.read_csv(csv_path)
        df = df.filter(items=['City', 'Country', 'ISO2', 'ISO3', 'State'])

        for index, row in df.iterrows():
            if not Locations.objects.filter(city=row.values[0], country=row.values[1], country_code_iso2=row.values[2],
                                            country_code_iso3=row.values[3], state=row.values[4]).count():
                print(f"added : {row}")
                Locations.objects.create(city=row['City'], country=row['Country']
                                         , country_code_iso2=row['ISO2'], country_code_iso3=row['ISO3'],
                                         state=row['State'])
            else:
                print(f"already present : {row}")
        print("---------------------Update Locations Command Ended----------------------")
