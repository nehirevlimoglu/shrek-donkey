from django.db import models
from tutorials.models.user_model import User

class Applicant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='applicant_profile')
    degree = models.CharField(max_length=150)
    cv = models.FileField(upload_to='uploads/cv/', blank=True, null=True)
    salary_preferences = models.CharField(max_length=100, blank=True)
    job_preferences = models.TextField(blank=True)
    location_preferences = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.degree}"
