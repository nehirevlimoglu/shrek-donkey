from django.db import models
from tutorials.models.employer_models import Job
from tutorials.models.user_model import User

class Applicant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    degree = models.CharField(max_length=255, blank=True, null=True)
    cv = models.FileField(upload_to='uploads/cv/', blank=True, null=True)
    salary_preferences = models.CharField(max_length=100, blank=True)
    job_preferences = models.TextField(blank=True)
    location_preferences = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.degree}"

class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('applied', 'Applied'),
        ('reviewed', 'Reviewed'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ], default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')  # Prevent duplicate applications

    def __str__(self):
        return f"{self.user.username} applied to {self.job.title}"

class FavoriteJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')  # Prevent duplicate favorites
