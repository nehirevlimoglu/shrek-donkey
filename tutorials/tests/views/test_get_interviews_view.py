import json
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Employer, Job, Interview, Candidate

User = get_user_model()

class GetInterviewsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        self.now_time = (timezone.now() + timedelta(hours=1)).time()

        # Create an employer user with role "Employer"
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.employer_user)

        # Create an Employer instance with the same username.
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",  # Must match request.user.username
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )

        # Create a Job associated with this employer.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job description",
            application_deadline=self.today + timedelta(days=10)
        )

        # Create a candidate user (applicant)
        self.candidate_user = User.objects.create_user(
            username="candidateuser",
            email="candidate@example.com",
            password="password123",
            role="Applicant"
        )

        # Create a Candidate instance for that user on the job.
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            job=self.job,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )

        # Create an Interview for the candidate.
        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=self.today + timedelta(days=1),
            time=time(10, 0),
            interview_link="http://example.com/interview",
            notes="Interview notes"
        )

        # URL for the view; adjust the URL name as needed.
        self.url = reverse("get_interviews")

    def test_get_interviews_success(self):
        """Test that a valid employer receives a JSON list of interview events."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Parse JSON response.
        events = response.json()
        # Expect at least one event.
        self.assertTrue(isinstance(events, list))
        self.assertGreaterEqual(len(events), 1)
        # Verify the structure of the first event.
        event = events[0]
        self.assertIn("id", event)
        self.assertIn("title", event)
        self.assertIn("start", event)
        self.assertIn("url", event)
        # Check that the title is formatted as expected.
        expected_title = f"Interview: {self.candidate.user.first_name} {self.candidate.user.last_name}"
        self.assertEqual(event["title"], expected_title)
        # Check the start field format contains a "T"
        self.assertIn("T", event["start"])
        # Check the URL is built using the interview id.
        expected_detail_url = f"/interview/{self.interview.pk}/"
        self.assertEqual(event["url"], expected_detail_url)

    def test_get_interviews_employer_not_found(self):
        """Test that if the logged-in user (with role Employer) does not have an Employer profile,
        the view returns a JSON error with status 403.
        """
        # Create a user with role "Employer" but DO NOT create an Employer profile.
        user_without_employer = User.objects.create_user(
            username="nouseremployer",
            email="nouseremployer@example.com",
            password="password123",
            role="Employer"  # This makes is_employer(user) return True.
        )
        self.client.force_login(user_without_employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Employer not found")


    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
