import json
import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from tutorials.models.employer_models import JobTitle

@receiver(post_migrate)
def populate_job_titles(sender, **kwargs):
    """Populate selectable job titles from JSON after migrations."""
    
    if sender.name != "tutorials":  # Ensure it runs only for the 'tutorials' app
        return

    json_path = os.path.join(settings.BASE_DIR, 'static/data/job_titles.json')

    if not os.path.exists(json_path):
        print(f"⚠️ Job titles file not found: {json_path}")
        return

    with open(json_path, 'r') as file:
        job_titles = json.load(file)

    added_titles = 0  # Counter for added job titles

    for title in job_titles:
        _, created = JobTitle.objects.get_or_create(title=title)
        if created:
            added_titles += 1

    print(f"✅ {added_titles} new job titles loaded from {json_path}")
