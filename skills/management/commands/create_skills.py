from django.core.management.base import BaseCommand
from skills.models import Skills  # Replace 'your_app' with the actual app name
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Load skills data from CSV and store it into the Skills model'

    def handle(self, *args, **kwargs):
        # Load and clean the data
        csv_path = os.path.join(os.path.dirname(__file__), 'skills.csv')
        skills_df = pd.read_csv(csv_path)

        # Remove any trailing newlines and whitespace
        skills_df['Skill'] = skills_df['Skill'].str.strip()

        # Get unique skills and save them to the database
        unique_skills = skills_df['Skill'].unique()
        for skill_name in unique_skills:
            skill, created = Skills.objects.get_or_create(name=skill_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully added skill: {skill_name}'))
            else:
                self.stdout.write(f'Skill already exists: {skill_name}')
