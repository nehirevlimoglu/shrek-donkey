from django.test import TestCase, Client
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from tutorials.models.employer_models import Candidate, Job, Employer
from tutorials.models.applicants_models import Applicant, Application  # Assuming this is where Applicant is defined
from tutorials.views.employer_views import calculate_duration  # Adjust if needed

User = get_user_model()

class ApplicantProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an applicant user.
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.applicant_user)
        
        # Create an Applicant profile for this user.
        self.applicant_obj = Applicant.objects.create(
            user=self.applicant_user,
            # Populate additional required fields as needed.
        )
        
        # Create an employer and job (needed for the application)
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job description",
            application_deadline=timezone.now().date() + timedelta(days=10)
        )
        
        # Create a Candidate instance (for employer view, candidate is used)
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            application_status="under_review",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )
        
        # Create an Application instance for this candidate and job.
        # For testing, we populate work_experience with one sample entry.
        self.application = Application.objects.create(
            applicant=self.applicant_obj,
            job=self.job,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            address="123 Test St",
            education=[],
            work_experience=[{
                "work_start_date": "2018-01-01",
                "work_end_date": "2020-01-01"
            }],
            current_job_title="Developer",
            current_employer="Some Company",
            linkedin_profile="",
            portfolio_website="",
            how_did_you_hear="other",
            sponsorship_needed="no",
            confirm_information=True,
            status="under_review"
        )
        
        # Build the URL for the view using candidate id.
        self.url = reverse("applicant_profile", kwargs={"applicant_id": self.candidate.id})

    def test_review_applicant_profile_success(self):
        """Test that a valid GET request returns the applicant profile review page with candidate and application in context,
        and that work experiences have a 'duration' key computed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicant_profile.html")
        self.assertIn("candidate", response.context)
        self.assertIn("application", response.context)
        
        # Check candidate.
        candidate_from_context = response.context["candidate"]
        self.assertEqual(candidate_from_context.id, self.candidate.id)
        
        # Check application and its work_experience duration.
        application = response.context["application"]
        self.assertIsNotNone(application)
        # There should be at least one work experience entry.
        self.assertTrue(len(application.work_experience) > 0)
        for work in application.work_experience:
            # The view should have added a 'duration' key.
            self.assertIn("duration", work)
            # We can compute the expected duration using calculate_duration.
            expected_duration = calculate_duration(work.get("work_start_date"), work.get("work_end_date"))
            self.assertEqual(work["duration"], expected_duration)

    def test_candidate_not_found(self):
        """Test that if a candidate with the given applicant_id does not exist, the view returns a 404 response."""
        invalid_url = reverse("applicant_profile", kwargs={"applicant_id": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Candidate does not exist", response.content.decode())

    def test_applicant_profile_not_found(self):
        """Test that if the Applicant profile is not found for the candidate's user, the view returns a 404 response."""
        # Delete the Applicant profile.
        self.applicant_obj.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Applicant profile not found", response.content.decode())

    def test_post_update_application_status(self):
        """Test that a POST request with a valid status updates the candidate's application_status and redirects back."""
        new_status = "Hired"
        data = {"status": new_status}
        response = self.client.post(self.url, data)
        # Expect a redirect back to the same view.
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse("applicant_profile", kwargs={"applicant_id": self.candidate.id})
        self.assertRedirects(response, expected_redirect)
        # Check that the candidate's status was updated.
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, new_status)

    def test_post_invalid_status_no_update(self):
        """Test that a POST with an invalid status does not update the candidate's status."""
        original_status = self.candidate.application_status
        data = {"status": "InvalidStatus"}
        response = self.client.post(self.url, data)
        # Even if status is invalid, view always redirects.
        self.assertEqual(response.status_code, 302)
        self.candidate.refresh_from_db()
        # The status should remain unchanged.
        self.assertEqual(self.candidate.application_status, original_status)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
