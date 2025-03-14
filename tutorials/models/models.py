from django.contrib.auth.models import AbstractUser
from django.db import models
from tutorials.models.employer_models import Job
from tutorials.models.applicants_models import Applicant  

class JobPosition(models.Model):
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_posts")
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    mission = models.TextField()
    description = models.TextField()
    minimum_criteria = models.TextField()
    desirable_criteria = models.TextField()
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

'''
class JobPosition(models.Model):
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_posts")
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    mission = models.TextField()
    description = models.TextField()
    minimum_criteria = models.TextField()
    desirable_criteria = models.TextField()
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
'''

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    education = models.TextField()
    experience = models.TextField()
    skills = models.TextField()
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)

    def __str__(self):
        return self.user.username

class Application(models.Model):
    job = models.ForeignKey(JobPosition, on_delete=models.CASCADE)
    job_seeker = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('applied', 'Applied'),
        ('reviewed', 'Reviewed'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ], default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.job_seeker.user.username} applied to {self.job.title}"
