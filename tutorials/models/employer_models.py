from django.core.validators import RegexValidator, MaxLengthValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from libgravatar import Gravatar
from tutorials.models.user_model import User
from django.utils import timezone
from datetime import date
import json


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
        ('Manufacturing', 'Manufacturing'),
        ('Construction', 'Construction'),
        ('Transportation', 'Transportation'),
        ('Hospitality', 'Hospitality'),
        ('Legal', 'Legal'),
        ('Government', 'Government'),
        ('Telecommunications', 'Telecommunications'),
        ('Real Estate', 'Real Estate'),
        ('Media', 'Media'),
        ('Entertainment', 'Entertainment'),
        ('Energy', 'Energy'),
        ('Agriculture', 'Agriculture'),
        ('Non-Profit', 'Non-Profit'),
        ('Consulting', 'Consulting'),
        ('Logistics', 'Logistics'),
        ('Automotive', 'Automotive'),
        ('Aerospace', 'Aerospace'),
        ('Defense', 'Defense'),
        ('Environmental Services', 'Environmental Services'),
        ('Food & Beverage', 'Food & Beverage'),
        ('Pharmaceuticals', 'Pharmaceuticals'),
        ('Fashion', 'Fashion'),
        ('Marketing', 'Marketing'),
        ('E-commerce', 'E-commerce'),
        ('Architecture', 'Architecture'),
        ('Sports', 'Sports'),
        ('Travel & Tourism', 'Travel & Tourism'),
        ('Biotechnology', 'Biotechnology'),
        ('Publishing', 'Publishing'),
        ('Cybersecurity', 'Cybersecurity'),
        ('Animation', 'Animation'),
        ('Human Resources', 'Human Resources'),
        ('Insurance', 'Insurance'),
        ('Mining', 'Mining'),
        ('Petroleum', 'Petroleum'),
        ('Other', 'Other'),
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
        return f"{self.company_name} ({self.username})"
    

class JobTitle(models.Model):
    title = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.title 
        return f"{self.company_name} ({self.user.username})"


class Job(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    title = models.CharField(max_length=255)  # ✅ Changed to CharField for free-text job titles
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
    created_at = models.DateTimeField(default=timezone.now)

    extracted_skills = models.TextField(blank=True, default="[]")
    required_experience = models.FloatField(
        null=True,
        blank=True,
        help_text="Minimum years of experience required for the job."
    )
    required_discipline = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Required academic or professional discipline for the job."
    )

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'  # New jobs start as pending
    )

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def get_extracted_skills(self):
        return json.loads(self.extracted_skills or "[]")

    def set_extracted_skills(self, skill_list):
        self.extracted_skills = json.dumps(skill_list)


class WorkExperience(models.Model):
    candidate = models.ForeignKey('Candidate', on_delete=models.CASCADE, related_name='work_experiences')
    job_title = models.CharField(max_length=255)
    employer = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Use today's date if not provided
    job_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.job_title} at {self.employer}"
    

class EmployerNotification(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField(default="No message provided")
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.employer.company_name}"

        

class Candidate(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Interview', 'Interview Scheduled'),
        ('Hired', 'Hired'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="candidates", null=True, blank=True)
    application_date = models.DateTimeField(auto_now_add=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)  # ✅ Already correct
    cover_letter = models.FileField(upload_to='cover_letters/', blank=True, null=True)  # ✅ Change this

    # Education fields
    school = models.CharField(max_length=255, blank=True, null=True)
    degree = models.CharField(max_length=255, blank=True, null=True)
    discipline = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    skills = models.TextField(blank=True, null=True, default="[]")

    current_job_title = models.CharField(max_length=255, blank=True, null=True)
    current_employer = models.CharField(max_length=255, blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    portfolio_website = models.URLField(blank=True, null=True)
    how_did_you_hear = models.CharField(max_length=255, blank=True, null=True)
    application_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.user.username} - {self.job.title if self.job else 'No Job Assigned'}"

    @property
    def total_experience_years(self):
        total_days = 0
        for exp in self.work_experiences.all():
            if exp.start_date:
                end_date = exp.end_date if exp.end_date else date.today()
                delta = (end_date - exp.start_date).days
                print(f"DEBUG: {self.user.username} - {exp.job_title}: Start {exp.start_date}, End {exp.end_date}, Days {delta}")
                total_days += delta
        return total_days / 365.25 if total_days > 0 else 0






class Interview(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="interviews")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="job_interviews")
    date = models.DateField()
    time = models.TimeField()
    interview_link = models.URLField(blank=True, null=True, help_text="Link for virtual interviews")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Interview for {self.candidate.user.username} - {self.job.title} on {self.date}"


class EmployerNotification(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField(default="No message provided")
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.employer.company_name}"


class EmployerEvent(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.employer.company_name}"
