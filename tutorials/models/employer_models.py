from django.core.validators import RegexValidator, MaxLengthValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar
from tutorials.models.user_model import User



class Employer(models.Model):
    # Link to the User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)  # New field added here
    company_name = models.CharField(max_length=255)
    company_website = models.URLField(blank=True, null=True)
    company_location = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, choices=[
        ('Tech', 'Tech'),
        ('Finance', 'Finance'),
        ('Healthcare', 'Healthcare'),
        ('Education', 'Education'),
        ('Retail', 'Retail'),
        ('Other', 'Other')
    ])
    company_size = models.PositiveIntegerField(default=1)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    total_jobs_posted = models.PositiveIntegerField(default=0)
    total_applicants = models.PositiveIntegerField(default=0)
    recent_activity = models.DateTimeField(auto_now=True)
    
    is_verified = models.BooleanField(default=False)
    account_status = models.CharField(max_length=20, choices=[
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Pending', 'Pending')
    ], default='Pending')
    subscription_plan = models.CharField(max_length=20, choices=[
        ('Free', 'Free'),
        ('Premium', 'Premium'),
        ('Enterprise', 'Enterprise')
    ], default='Free')

    def __str__(self):
        return f"{self.company_name} ({self.user.username})"


class Job(models.Model):
    employer = models.ForeignKey(
        Employer,
        on_delete=models.CASCADE,
        related_name='jobs',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=255, default="Unknown Company")
    location = models.CharField(max_length=255, default="Unknown Location")
    job_type = models.CharField(
        max_length=100,
        choices=[
            ('Full Time', 'Full Time'),
            ('Part Time', 'Part Time'),
            ('Internship', 'Internship'),
            ('Apprenticeship', 'Apprenticeship')
        ],
        blank=True,
        null=True
    )
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    benefits = models.TextField(blank=True, null=True)
    application_deadline = models.DateField(null=True, blank=True)
    contact_email = models.EmailField(default="default@email.com")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Candidate(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Interview', 'Interview Scheduled'),
        ('Hired', 'Hired'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="candidates")
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    cover_letter = models.TextField(blank=True, null=True)
    application_date = models.DateTimeField(auto_now_add=True)
    application_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"

class Interview(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="interviews")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="job_interviews")
    date = models.DateField()
    time = models.TimeField()
    interview_link = models.URLField(blank=True, null=True, help_text="Link for virtual interviews")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Interview for {self.candidate.user.username} - {self.job.title} on {self.date}"
