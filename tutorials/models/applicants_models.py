from django.db import models
from tutorials.models.user_model import User
from tutorials.models.employer_models import Job


class Applicant(models.Model):
    """ Stores applicant information, linked to a User """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    degree = models.CharField(max_length=255, blank=True, null=True)
    cv = models.FileField(upload_to="uploads/cv/", blank=True, null=True)
    salary_preferences = models.CharField(max_length=100, blank=True)
    job_preferences = models.TextField(blank=True)
    location_preferences = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.degree if self.degree else 'No Degree'}"


class Application(models.Model):
    """ Stores job application details for each applicant """
    
    STATUS_CHOICES = [
        ("under_review", "Under Review"),
        ("interviewed", "Interviewed"),
        ("hired", "Hired"),
        ("rejected", "Rejected"),
    ]

    applicant = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")

    # Personal Details
    first_name = models.CharField(max_length=50, default="Unknown")
    last_name = models.CharField(max_length=50, default="Unknown")
    email = models.EmailField(max_length=100, default="Unknown")
    phone = models.CharField(max_length=20, default="Unknown")
    address = models.CharField(max_length=255, default="Unknown")

    # Resume & Cover Letter
    resume = models.FileField(upload_to="uploads/resumes/", blank=True, null=True)
    cover_letter = models.FileField(upload_to="uploads/cover_letters/", blank=True, null=True)

    # Education (Stores Multiple Entries as JSON)
    education = models.JSONField(default=list)  # Stores multiple education entries dynamically

    # Current Job Details
    current_job_title = models.CharField(max_length=100, default="Not Specified")
    current_employer = models.CharField(max_length=100, default="Not Specified")
    linkedin_profile = models.URLField(blank=True, null=True)
    portfolio_website = models.URLField(blank=True, null=True)

    # Additional Questions
    how_did_you_hear = models.CharField(
        max_length=50,
        choices=[
            ("linkedin", "LinkedIn"),
            ("website", "Company Website"),
            ("referral", "Referral"),
            ("other", "Other"),
        ],
        default="other",
    )

    sponsorship_needed = models.CharField(
        max_length=3, choices=[("yes", "Yes"), ("no", "No")], default="no"
    )

    confirm_information = models.BooleanField(default=False)

    # Application Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="under_review"
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.username} - {self.job.title}"
