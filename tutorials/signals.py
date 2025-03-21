import json
import os
from django.db.models.signals import post_migrate, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.conf import settings
from tutorials.models.employer_models import JobTitle
from tutorials.models.employer_models import Job, Candidate, Employer
from django.utils.timezone import now
from .models.admin_models import Notification, Admin
from .models.user_model import User
from .views.admin_views import create_admin_notification


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

# Create notifications for admin users when important events occur


@receiver(post_save, sender=Job)
def job_creation_notification(sender, instance, created, **kwargs):
    """Send notification to admins when a new job is created"""
    if created:
        admins = User.objects.filter(role='Admin')
        for admin in admins:
            create_admin_notification(
                admin,
                "New Job Listing Created",
                f"A new job '{instance.title}' has been posted by {instance.company_name}.",
                notification_type='job',
                priority='medium',
                related_object_id=instance.id,
                related_object_type='job',
                action_url=f'/admin_job_detail/{instance.id}/'
            )

@receiver(post_save, sender=Candidate)
def application_notification(sender, instance, created, **kwargs):
    """Send notification to admins when a new application is submitted"""
    if created:
        admins = User.objects.filter(role='Admin')
        for admin in admins:
            create_admin_notification(
                admin,
                "New Job Application",
                f"A new application has been submitted for '{instance.job.title}' at {instance.job.company_name}.",
                notification_type='application',
                priority='high',
                related_object_id=instance.id,
                related_object_type='application'
            )

@receiver(post_save, sender=User)
def new_user_notification(sender, instance, created, **kwargs):
    """Send notification to admins when a new user registers"""
    if created and instance.role != 'Admin':  # Don't notify for admin creations
        admins = User.objects.filter(role='Admin')
        for admin in admins:
            create_admin_notification(
                admin,
                "New User Registration",
                f"A new user ({instance.get_full_name()}) has registered with role: {instance.role}.",
                notification_type='user',
                priority='medium',
                related_object_id=instance.id,
                related_object_type='user'
            )

#@receiver(post_save, sender=Candidate)
#def application_status_change(sender, instance, created, **kwargs):
 #   """Send notification when application status changes"""
  #  if not created and instance.tracker.has_changed('application_status'):
   #     admins = User.objects.filter(role='Admin')
    #    for admin in admins:
     #       create_admin_notification(
      #          admin,
       #         "Application Status Change",
        #        f"The status of an application for '{instance.job.title}' has changed to '{instance.application_status}'."
         #   )

@receiver(post_save, sender=Candidate)
def application_status_changed(sender, instance, created, **kwargs):
    """
    Send notification when application status changes
    This replaces the previous function that used tracker
    """
    if not created:  # Only for updates, not new applications
        admins = User.objects.filter(role='Admin')
        for admin in admins:
            create_admin_notification(
                admin,
                "Application Status Update",
                f"The status of an application from {instance.user.get_full_name()} for '{instance.job.title}' position at {instance.job.company_name} is now '{instance.application_status}'.",
                notification_type='application',
                priority='high' if instance.application_status in ['Hired', 'Rejected'] else 'medium',
                related_object_id=instance.id,
                related_object_type='application'
            )

@receiver(post_delete, sender=Job)
def job_deletion_notification(sender, instance, **kwargs):
    """Send notification when a job is deleted"""
    admins = User.objects.filter(role='Admin')
    for admin in admins:
        create_admin_notification(
            admin,
            "Job Listing Deleted",
            f"The job listing '{instance.title}' at {instance.company_name} has been deleted.",
            notification_type='job',
            priority='high'
        )
