from django.db import models
from tutorials.models.user_model import User

class Applicant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    degree = models.CharField(max_length=200, default="")
    min_salary_preference = models.IntegerField(
        help_text="Enter your minimum expected annual salary",
        null=True,
        blank=True
    )
    max_salary_preference = models.IntegerField(
        help_text="Enter your maximum expected annual salary",
        null=True,
        blank=True
    )
    job_preferences = models.TextField(default="")
    location_preferences = models.CharField(max_length=200, default="")
    cv = models.FileField(upload_to='cvs/', null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_formatted_salary(self):
        if self.min_salary_preference and self.max_salary_preference:
            return f"${self.min_salary_preference:,} - ${self.max_salary_preference:,}/year"
        elif self.min_salary_preference:
            return f"From ${self.min_salary_preference:,}/year"
        elif self.max_salary_preference:
            return f"Up to ${self.max_salary_preference:,}/year"
        return "Not specified"
