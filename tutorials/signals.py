import json
import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from tutorials.models.employer_models import Job
from django.utils.timezone import now

@receiver(post_migrate)
def populate_jobs(sender, **kwargs):
    """ Automatically populate job titles from JSON after migrations. """
    
    if sender.name != "tutorials":  # Ensure it runs only for the 'tutorials' app
        return

    json_path = os.path.join(settings.BASE_DIR, 'static/data/job_titles.json')

    if not os.path.exists(json_path):
        print(f"⚠️ Job titles file not found: {json_path}")
        return

    with open(json_path, 'r') as file:
        job_titles = json.load(file)

    added_jobs = 0  # Counter for added jobs

    for title in job_titles:
        job, created = Job.objects.get_or_create(
            title=title,
            defaults={
                "company_name": "Unknown Company",
                "location": "Unknown Location",
                "job_type": "Full Time",
                "salary": 50000.00,
                "description": f"{title} job description.",
                "requirements": "Basic job requirements.",
                "benefits": "Standard company benefits.",
                "application_deadline": now().date(),
                "contact_email": "default@email.com"
            }
        )
        if created:
            added_jobs += 1

    print(f"✅ {added_jobs} new job titles loaded from {json_path}")
