from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job, Employer
from tutorials.forms.employer_forms import JobForm

User = get_user_model()

class EditJobViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.user)

        self.employer = Employer.objects.create(
            user=self.user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title="Original Title",
            description="Original job description",
            application_deadline=timezone.now().date() + timedelta(days=10),
            status="pending"
        )

        self.url = reverse("job_edit", kwargs={"pk": self.job.pk})

    def test_get_edit_job_view(self):
        """Test GET request loads the edit job page with form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_job.html")
        self.assertIn("job", response.context)
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertIsInstance(form, JobForm)
        self.assertEqual(form.initial.get("title", ""), self.job.title)

    def test_post_valid_edit_job_view(self):
        """Test POST with valid data updates the job and redirects."""
        updated_data = {
            "title": "Updated Title",
            "position": "Updated Position",
            "company_name": self.employer.company_name,
            "location": self.employer.company_location,
            "job_type": "Full Time",
            "salary": 75000,
            "description": "Updated description",
            "requirements": "Updated requirements",
            "benefits": "Updated benefits",
            "application_deadline": (timezone.now().date() + timedelta(days=20)).isoformat(),
            "contact_email": self.employer.email,
        }
        response = self.client.post(self.url, updated_data)
        expected_redirect = reverse("employer_job_detail", kwargs={"job_id": self.job.pk})  # ✅

        self.assertRedirects(response, expected_redirect)

        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Updated Title")
        self.assertEqual(self.job.salary, 75000)
        self.assertEqual(self.job.description, "Updated description")
        self.assertEqual(self.job.requirements, "Updated requirements")
        self.assertEqual(self.job.benefits, "Updated benefits")
        self.assertEqual(self.job.contact_email, self.employer.email)

    def test_post_invalid_edit_job_view(self):
        """Test POST with invalid data (e.g., missing title) shows form with errors."""
        invalid_data = {
            "title": "",
            "position": "Updated Position",
            "company_name": self.employer.company_name,
            "location": self.employer.company_location,
            "job_type": "Full Time",
            "salary": 75000,
            "description": "Updated description",
            "requirements": "Updated requirements",
            "benefits": "Updated benefits",
            "application_deadline": (timezone.now().date() + timedelta(days=20)).isoformat(),
            "contact_email": self.employer.email,
        }
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_job.html")
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("title", form.errors)