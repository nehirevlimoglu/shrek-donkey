from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Employer, Job, Interview, Candidate

User = get_user_model()

class EmployerCalendarViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        # Create an employer user with role "Employer"
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.employer_user)
        
        # Create an Employer instance linked to the user.
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
            description="Description for Test Job",
            application_deadline=self.today + timedelta(days=10)
        )
        
        # Create a candidate for this job.
        # For clarity, create a separate applicant user.
        self.applicant_user = User.objects.create_user(
            username="candidateuser",
            email="candidate@example.com",
            password="password123",
            role="Applicant"
        )
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )
        
        # Create Interview objects using the valid candidate.
        self.interview1 = Interview.objects.create(
            candidate=self.candidate,  # Now a valid candidate instance
            job=self.job,
            date=self.today + timedelta(days=1),
            time=timezone.now().time(),
            interview_link="http://example.com/interview1",
            notes="Interview 1 notes"
        )
        self.interview2 = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=self.today + timedelta(days=2),
            time=timezone.now().time(),
            interview_link="http://example.com/interview2",
            notes="Interview 2 notes"
        )
        
        # Build the URL for the view.
        self.url = reverse("employer_calendar")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_forbidden_if_not_employer(self):
        """Test that a logged-in user without an Employer profile gets a 403 Forbidden."""
        # Create a non-employer user.
        non_employer = User.objects.create_user(
            username="nonemployer",
            email="nonemployer@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(non_employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_employer_calendar_view(self):
        """Test that a GET request for an employer returns the calendar with interviews."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer_calendar.html")
        self.assertIn("interviews", response.context)
        interviews = response.context["interviews"]
        # Expect both interview objects to be present.
        self.assertEqual(interviews.count(), 2)
