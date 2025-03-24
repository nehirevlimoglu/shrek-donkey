from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job, Employer

User = get_user_model()

class AdminEditJobViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user with necessary flags
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        
        # Create an employer (if needed by the job) linked to the admin user
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )
        
        # Create a job to edit
        self.job = Job.objects.create(
            employer=self.employer,
            title="Original Title",
            company_name="Original Company",
            location="Original Location",
            job_type="Full Time",
            salary=50000,
            description="Original description",
            requirements="Original requirements",
            benefits="Original benefits",
            application_deadline=timezone.now().date() + timedelta(days=10),
            contact_email="contact@original.com",
            created_at=timezone.now()
        )
        self.url = reverse("admin_edit_job", kwargs={"job_id": self.job.id})

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to login."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_non_admin_user_redirected(self):
        """Test that a logged-in non-admin user is redirected."""
        # Create a non-admin user.
        non_admin = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(non_admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_edit_job_page(self):
        """Test that a GET request returns the admin edit job page with job context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_edit_job.html")
        self.assertIn("job", response.context)
        self.assertEqual(response.context["job"].id, self.job.id)

    def test_post_edit_job_updates_fields(self):
        """Test that a POST request updates job fields and redirects to job detail page."""
        new_data = {
            "title": "Updated Title",
            "company_name": "Updated Company",
            "location": "Updated Location",
            "job_type": "Part Time",
            "salary": "75000",  # salary sent as string from POST data
            "description": "Updated description",
            "requirements": "Updated requirements",
            "benefits": "Updated benefits",
            "application_deadline": (timezone.now().date() + timedelta(days=20)).isoformat(),
            "contact_email": "contact@updated.com",
        }
        response = self.client.post(self.url, new_data)
        # Expect redirect to admin_job_detail
        expected_redirect = reverse("admin_job_detail", kwargs={"job_id": self.job.id})
        self.assertRedirects(response, expected_redirect)

        # Reload the job from the database and verify updates.
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, new_data["title"])
        self.assertEqual(self.job.company_name, new_data["company_name"])
        self.assertEqual(self.job.location, new_data["location"])
        self.assertEqual(self.job.job_type, new_data["job_type"])
        self.assertEqual(self.job.salary, int(new_data["salary"]))
        self.assertEqual(self.job.description, new_data["description"])
        self.assertEqual(self.job.requirements, new_data["requirements"])
        self.assertEqual(self.job.benefits, new_data["benefits"])
        # Compare deadline as date object.
        self.assertEqual(self.job.application_deadline.isoformat(), new_data["application_deadline"])
        self.assertEqual(self.job.contact_email, new_data["contact_email"])
