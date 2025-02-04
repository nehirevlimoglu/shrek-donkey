from django.core.validators import RegexValidator, MaxLengthValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar
from tutorials.models.user_model import User

class Employer(User):
    company_name = models.CharField(max_length=255)
    company_website = models.URLField(blank=True, null=True)
    company_location = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, choices=[
        ('Tech', 'Tech'), ('Finance', 'Finance'), ('Healthcare', 'Healthcare'),
        ('Education', 'Education'), ('Retail', 'Retail'), ('Other', 'Other')
    ])
    job_type = models.CharField(max_length=100, choices=[
        ('Full Time', 'Full Time'), ('Part Time', 'Part Time'), 
        ('Internship', 'Internship'),('Apprenticeship', 'Apprenticeship')
    ])
    company_size = models.IntegerField(default=1)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    total_jobs_posted = models.IntegerField(default=0)
    total_applicants = models.IntegerField(default=0)
    recent_activity = models.DateTimeField(auto_now=True)
    
    is_verified = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'), ('Suspended', 'Suspended'), ('Pending', 'Pending')
    ], default='Pending')
    subscription_plan = models.CharField(max_length=20, choices=[
        ('Free', 'Free'), ('Premium', 'Premium'), ('Enterprise', 'Enterprise')
    ], default='Free')

    def __str__(self):
        return f"{self.company_name} ({self.username})"