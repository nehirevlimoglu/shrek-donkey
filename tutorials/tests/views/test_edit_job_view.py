from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job, Employer
from tutorials.forms.employer_forms import JobForm  # Adjust import as needed

User = get_user_model()

class EditJobViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user with role "Employer"
        self.user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        # Log in the user.
        self.client.force_login(self.user)
        
        # Create an Employer instance linked to the user.
        self.employer = Employer.objects.create(
            user=self.user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        
        # Create a Job instance for testing.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Original Title",
            description="Original job description",
            application_deadline=timezone.now().date() + timedelta(days=10),
            status="pending"
        )
        # Use the URL name "job_edit" as defined in your URLconf:
        self.url = reverse("job_edit", kwargs={"pk": self.job.pk})

    def test_get_edit_job_view(self):
        """Test that a GET request returns the edit job page with a pre-filled form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Check that our dummy template is used.
        self.assertIn("dummy content", response.content.decode())
        self.assertIn("job", response.context)
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertIsInstance(form, JobForm)
        self.assertEqual(form.initial.get("title", ""), self.job.title)

    def test_post_valid_edit_job_view(self):
        """Test that a valid POST updates the job and redirects to the job detail view."""
        updated_data = {
            "title": "Updated Title",
            "position": "Updated Position",  # if your form includes this field
            "company_name": self.job.employer.company_name,  # using employer default
            "location": self.job.employer.company_location,    # using employer default
            "job_type": "Full Time",  # example
            "salary": 75000,
            "description": "Updated description",
            "requirements": "Updated requirements",
            "benefits": "Updated benefits",
            "application_deadline": (timezone.now().date() + timedelta(days=20)).isoformat(),
            "contact_email": self.job.employer.email,  # using employer default
        }
        response = self.client.post(self.url, updated_data)
        # Expect redirect to job_detail_view; note that the view expects job_id, not pk.
        expected_redirect = reverse("employer_job_detail", kwargs={"job_id": self.job.pk})
        self.assertRedirects(response, expected_redirect)
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Updated Title")
        self.assertEqual(self.job.salary, 75000)
        self.assertEqual(self.job.description, "Updated description")
        self.assertEqual(self.job.requirements, "Updated requirements")
        self.assertEqual(self.job.benefits, "Updated benefits")
        self.assertEqual(self.job.contact_email, self.job.employer.email)
        self.assertEqual(self.job.application_deadline.isoformat(), updated_data["application_deadline"])

    def test_post_invalid_edit_job_view(self):
        """Test that an invalid POST (e.g., missing required title) re-renders the form with errors."""
        invalid_data = {
            "title": "",  # required field left blank
            "position": "Updated Position",
            "company_name": self.job.employer.company_name,
            "location": self.job.employer.company_location,
            "job_type": "Full Time",
            "salary": 75000,
            "description": "Updated description",
            "requirements": "Updated requirements",
            "benefits": "Updated benefits",
            "application_deadline": (timezone.now().date() + timedelta(days=20)).isoformat(),
            "contact_email": self.job.employer.email,
        }
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, 200)
        # Even though our dummy template is used, we can check that the view re-renders
        self.assertIn("dummy content", response.content.decode())
        form = response.context["form"]
        self.assertTrue(form.errors)