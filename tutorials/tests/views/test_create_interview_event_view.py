from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from tutorials.forms.employer_forms import InterviewForm
from tutorials.models.employer_models import Interview, Candidate, Job, Employer
from django.contrib.auth import get_user_model

User = get_user_model()

class InterviewFormTests(TestCase):
    def setUp(self):
        # Create a user (could be an applicant)
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            role="Applicant"
        )
        # Create an Employer (if needed for Job)
        self.employer = Employer.objects.create(
            user=self.user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        # Create a Job instance (associated with the employer)
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job description for testing",
            application_deadline=timezone.now().date() + timedelta(days=10)
        )
        # Create a Candidate (associated with the user and job)
        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )

    def test_valid_form(self):
        """Test that a form with valid data is valid."""
        form_data = {
            "candidate": self.candidate.id,
            "job": self.job.id,
            "date": (timezone.now().date() + timedelta(days=1)).isoformat(),
            "time": "10:00:00",
            "interview_link": "http://example.com/interview",
            "notes": "This is a test interview."
        }
        form = InterviewForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_field(self):
        """Test that a form missing a required field is invalid."""
        # Remove the candidate field which is required.
        form_data = {
            # "candidate": self.candidate.id,  <-- missing candidate
            "job": self.job.id,
            "date": (timezone.now().date() + timedelta(days=1)).isoformat(),
            "time": "10:00:00",
            "interview_link": "http://example.com/interview",
            "notes": "This is a test interview."
        }
        form = InterviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("candidate", form.errors)
