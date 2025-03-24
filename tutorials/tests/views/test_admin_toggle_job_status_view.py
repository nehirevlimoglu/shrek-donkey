import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Job, Employer

User = get_user_model()

class AdminToggleJobStatusViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        # Create an admin user with necessary flags.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        
        # Create an Employer instance linked to the admin user.
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )
        
        # Create a job for testing.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="A test job.",
            application_deadline=self.today + timedelta(days=10),
            status="pending"
        )
        
        # URL for toggling job status; ensure URL name matches your URL config.
        self.url = reverse("admin_toggle_job_status", kwargs={"job_id": self.job.id})

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.url, data=json.dumps({"status": "Closed"}), content_type="application/json")
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_invalid_method_get(self):
        """Test that GET requests are not allowed (405 Method Not Allowed)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_toggle_job_status_closed(self):
        """Test that toggling status to 'Closed' sets deadline to yesterday."""
        new_status = "Closed"
        response = self.client.post(self.url, data=json.dumps({"status": new_status}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data.get("success"))
        
        self.job.refresh_from_db()
        expected_deadline = timezone.now().date() - timedelta(days=1)
        self.assertEqual(self.job.application_deadline, expected_deadline)

    def test_toggle_job_status_open(self):
        """Test that toggling status to 'Open' sets deadline to 30 days in the future."""
        new_status = "Open"
        response = self.client.post(self.url, data=json.dumps({"status": new_status}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data.get("success"))
        
        self.job.refresh_from_db()
        expected_deadline = timezone.now().date() + timedelta(days=30)
        self.assertEqual(self.job.application_deadline, expected_deadline)

    def test_toggle_job_status_approved(self):
        """Test that toggling status to 'Approved' sets job status to 'approved'
           and, if deadline is past, updates it to 30 days in the future.
        """
        new_status = "Approved"
        # Set deadline to past so that it needs updating.
        self.job.application_deadline = self.today - timedelta(days=1)
        self.job.save()
        
        response = self.client.post(self.url, data=json.dumps({"status": new_status}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data.get("success"))
        
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "approved")
        expected_deadline = timezone.now().date() + timedelta(days=30)
        self.assertEqual(self.job.application_deadline, expected_deadline)
