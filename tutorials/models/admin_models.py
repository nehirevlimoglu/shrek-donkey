from django.core.validators import RegexValidator, MaxLengthValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar
from tutorials.models.user_model import User
from django.utils import timezone

class Admin(User):
    phone_validator = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_validator], max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username

class Notification(models.Model):
    # Notification type choices
    TYPE_GENERAL = 'general'
    TYPE_JOB = 'job'
    TYPE_APPLICATION = 'application'
    TYPE_USER = 'user'
    TYPE_SYSTEM = 'system'
    
    TYPE_CHOICES = [
        (TYPE_GENERAL, 'General'),
        (TYPE_JOB, 'Job Listing'),
        (TYPE_APPLICATION, 'Application'),
        (TYPE_USER, 'User'),
        (TYPE_SYSTEM, 'System'),
    ]
    
    # Priority choices
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='sent_notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField(default="No message provided")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    action_url = models.CharField(max_length=255, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.recipient:
            return f"{self.title} - {self.recipient.username}"
        return self.title
        
    def mark_as_read(self):
        self.is_read = True
        self.save()
        
    def soft_delete(self):
        self.is_deleted = True
        self.save()

class NotificationPreference(models.Model):
    admin = models.OneToOneField(Admin, on_delete=models.CASCADE, related_name='notification_preferences')
    job_notifications = models.BooleanField(default=True)
    application_notifications = models.BooleanField(default=True)
    user_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    
    email_delivery = models.BooleanField(default=True)
    dashboard_delivery = models.BooleanField(default=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification Preferences for {self.admin.username}"