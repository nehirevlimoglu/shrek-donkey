import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Candidate, Employer, Job
from tutorials.models.admin_models import Notification  # Adjust as needed

User = get_user_model()

class GetCandidateInfoViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user that will pass is_admin.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        
        # Create an Employer instance (if needed for candidate-job relationship)
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )
        
        # Create a Job instance to assign to the candidate.
        self.job_instance = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job for testing candidate info",
            application_deadline=timezone.now().date() + timedelta(days=10)
        )
        
        # Create a Candidate using the job_instance.
        self.candidate = Candidate.objects.create(
            user=self.admin_user,  # for simplicity, using the same admin user as candidate
            job=self.job_instance,  # assign the created job
            application_status="Pending",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe",
            phone="123-456-7890",
            degree="Bachelor",
            school="Test University",
            skills='["Python", "Django"]'
        )
        
        # Build the URL for get_candidate_info view.
        # Ensure the URL name "get_candidate_info" exists in your URL config.
        self.url = reverse("get_candidate_info", kwargs={"candidate_id": self.candidate.id})

    def test_get_candidate_info_success(self):
        """Test that a valid candidate ID returns the correct JSON data with CORS headers."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        # Parse JSON and verify keys.
        data = response.json()
        self.assertEqual(data["id"], self.candidate.id)
        expected_name = f"{self.candidate.user.first_name} {self.candidate.user.last_name}" if self.candidate.user.first_name else self.candidate.user.username
        self.assertEqual(data["name"], expected_name)
        self.assertEqual(data["email"], self.candidate.user.email)
        # Check that application_date is formatted (if set)
        if self.candidate.application_date:
            self.assertEqual(data["application_date"], self.candidate.application_date.strftime('%Y-%m-%d'))
        self.assertEqual(data["status"], self.candidate.application_status)
        self.assertEqual(data["phone"], self.candidate.phone or "Not provided")
        self.assertEqual(data["degree"], self.candidate.degree or "Not provided")
        self.assertEqual(data["school"], self.candidate.school or "Not provided")
        self.assertEqual(data["skills"], self.candidate.skills or "[]")
        
        # Verify CORS headers are present.
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        self.assertEqual(response["Access-Control-Allow-Methods"], "GET, OPTIONS")
        self.assertEqual(response["Access-Control-Allow-Headers"], "X-Requested-With, Content-Type")

    def test_get_candidate_info_not_found(self):
        """Test that a candidate ID that does not exist returns a 404 error JSON."""
        invalid_url = reverse("get_candidate_info", kwargs={"candidate_id": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Candidate not found")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_non_admin_user_redirected(self):
        """Test that a logged-in user without admin privileges is redirected."""
        # Create a non-admin user.
        non_admin = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(non_admin)
        response = self.client.get(self.url)
        # Expect a redirect since the user does not pass the is_admin check.
        self.assertEqual(response.status_code, 302)
