from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Candidate
# Adjust the import for your view if needed.

User = get_user_model()

class RejectCandidateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a candidate user.
        self.candidate_user = User.objects.create_user(
            username="candidateuser",
            email="candidate@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.candidate_user)
        
        # Create a Candidate instance with an initial status that is not "Hired" or "Rejected".
        # We'll assume the default status is "under_review".
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            # Assume job is required; if so, you may need to create a dummy Job instance.
            job=None,  # If job is not required for status rejection, otherwise create a dummy job.
            application_status="under_review",
            application_date="2025-01-01",  # example value; adjust as needed.
            first_name="John",
            last_name="Doe"
        )
        # Build the URL for the view.
        self.url = reverse("reject_candidate", kwargs={"candidate_id": self.candidate.id})

    def test_reject_candidate_success(self):
        """Test that a candidate with a status not in ['Hired', 'Rejected'] is updated to 'Rejected'."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("message"), "Candidate rejected successfully!")
        self.assertEqual(data.get("status"), "Rejected")
        # Refresh candidate and verify status update.
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, "Rejected")

    def test_reject_candidate_already_hired(self):
        """Test that if a candidate's status is already 'Hired', a POST returns a 400 error."""
        self.candidate.application_status = "Hired"
        self.candidate.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get("error"), "Status cannot be changed once set.")

    def test_reject_candidate_already_rejected(self):
        """Test that if a candidate's status is already 'Rejected', a POST returns a 400 error."""
        self.candidate.application_status = "Rejected"
        self.candidate.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get("error"), "Status cannot be changed once set.")

    def test_candidate_not_found(self):
        """Test that an invalid candidate_id returns a 404 response."""
        invalid_url = reverse("reject_candidate", kwargs={"candidate_id": 99999})
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        # Use a fresh client instance that is not logged in.
        new_client = Client()
        response = new_client.post(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
