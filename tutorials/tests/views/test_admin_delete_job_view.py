from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job, Employer

User = get_user_model()

class AdminDeleteJobViewTests(TestCase):
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
        
        # Create an employer linked to the admin user
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )
        
        # Create a job to be deleted
        self.job = Job.objects.create(
            employer=self.employer,
            title="Job To Delete",
            description="Job description",
            application_deadline=timezone.now().date() + timedelta(days=10),
            created_at=timezone.now()
        )
        self.url = reverse("admin_delete_job", kwargs={"job_id": self.job.id})
    
    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
    
    def test_invalid_method_get(self):
        """Test that a GET request is not allowed (405 Method Not Allowed)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
    
    def test_delete_job_successful(self):
        """Test that a valid POST request deletes the job and returns JSON success."""
        # Ensure the job exists before deletion
        self.assertTrue(Job.objects.filter(id=self.job.id).exists())
        
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data.get("status"), "success")
        
        # Verify that the job no longer exists
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())
