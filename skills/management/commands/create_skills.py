from django.core.management.base import BaseCommand
from skills.models import Skills
import pandas as pd
import os
from django.db.utils import IntegrityError

class Command(BaseCommand):
    help = 'Load skills data from CSV and store them in the Skills model, only processing skills that include "python"'

    def handle(self, *args, **kwargs):
        # Define the path to the CSV file
        csv_path = os.path.join(os.path.dirname(__file__), 'skills.csv')
        
        # Load and clean the data
        try:
            skills_df = pd.read_csv(csv_path)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {csv_path}'))
            return

        # Ensure the CSV has a column named 'Skill'
        if 'Skill' not in skills_df.columns:
            self.stderr.write(self.style.ERROR("CSV must contain a column named 'Skill'"))
            return

        # Clean up the data by stripping whitespace and converting to lowercase
        skills_df['Skill'] = skills_df['Skill'].str.strip().str.lower()

        # Track the number of skills added and skipped
        skills_added = 0
        skills_skipped = 0

        for skill_name in skills_df['Skill']:
            
            try:
                # Try to create the skill
                skill, created = Skills.objects.get_or_create(name=skill_name)
                if created:
                    skills_added += 1
                    self.stdout.write(self.style.SUCCESS(f'Successfully added skill: {skill_name}'))
                else:
                    skills_skipped += 1
                    self.stdout.write(self.style.WARNING(f'Skill already exists, skipped: {skill_name}'))
            except IntegrityError:
                self.stderr.write(self.style.ERROR(f"Integrity error occurred while adding skill: {skill_name}"))

        # Print a summary
        self.stdout.write(self.style.SUCCESS(f'Total skills added: {skills_added}'))
        self.stdout.write(self.style.WARNING(f'Total skills skipped (duplicates): {skills_skipped}'))
