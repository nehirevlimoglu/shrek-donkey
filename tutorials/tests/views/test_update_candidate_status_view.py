import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Candidate, Employer, Job
# Assume Candidate.STATUS_CHOICES is defined, e.g.,
# Candidate.STATUS_CHOICES = [('Pending', 'Pending'), ('Interview', 'Interview Scheduled'), ('Hired', 'Hired'), ('Rejected', 'Rejected')]

User = get_user_model()

class UpdateCandidateStatusViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user (with flags so that is_admin passes)
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        
        # Create an Employer instance (if required)
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )
        
        # Create a valid Job instance to assign to the candidate.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="A test job for candidate status update",
            application_deadline=timezone.now().date() + timedelta(days=10)
        )
        
        # Create a Candidate for testing with a valid job instance.
        self.candidate = Candidate.objects.create(
            user=self.admin_user,  # using admin for simplicity
            job=self.job,          # assign the valid job instance
            application_status="Pending",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe",
            phone="123-456-7890",
            degree="Bachelor",
            school="Test University",
            skills='["Python", "Django"]'
        )
        self.url = reverse("update_candidate_status", kwargs={"candidate_id": self.candidate.id})

    def test_successful_update(self):
        """Test that a valid POST request updates the candidate's status."""
        new_status = "Hired"
        payload = {"status": new_status}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, new_status)

    def test_missing_status(self):
        """Test that missing status in the request returns a 400 error."""
        payload = {}  # no status provided
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Status is required")

    def test_invalid_status(self):
        """Test that providing an invalid status returns a 400 error with a valid options message."""
        payload = {"status": "InvalidStatus"}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        valid_statuses = [s[0] for s in Candidate.STATUS_CHOICES]
        expected_message = f'Invalid status. Valid options are: {", ".join(valid_statuses)}'
        self.assertEqual(data["error"], expected_message)

    def test_candidate_not_found(self):
        """Test that a non-existent candidate returns a 404 error."""
        invalid_url = reverse("update_candidate_status", kwargs={"candidate_id": 99999})
        payload = {"status": "Hired"}
        response = self.client.post(invalid_url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Candidate not found")

    def test_invalid_json(self):
        """Test that invalid JSON in the request returns a 400 error."""
        response = self.client.post(self.url, data="this is not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Invalid JSON in request body")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected."""
        self.client.logout()
        payload = {"status": "Hired"}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
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
        payload = {"status": "Hired"}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 302)
