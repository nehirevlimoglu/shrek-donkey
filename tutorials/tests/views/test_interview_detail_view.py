from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.http import Http404
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Interview, Job, Employer, Candidate

User = get_user_model()

class InterviewDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user (e.g., an applicant) for candidate and interview.
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            role="Applicant"
        )
        # Create an Employer (for the Job)
        self.employer = Employer.objects.create(
            user=self.user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        # Create a Job instance.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job description for testing",
            application_deadline=timezone.now().date() + timedelta(days=10)
        )
        # Create a Candidate instance.
        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )
        # Create an Interview instance.
        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=timezone.now().date() + timedelta(days=1),
            time=timezone.now().time(),
            interview_link="http://example.com/interview",
            notes="Interview notes for testing"
        )
        # Build the URL for interview_detail view.
        self.url = reverse("interview_detail", kwargs={"pk": self.interview.pk})

    def test_interview_detail_view_success(self):
        """Test that a valid interview id returns the interview detail page with correct context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "interview_detail.html")
        self.assertIn("interview", response.context)
        self.assertEqual(response.context["interview"].pk, self.interview.pk)

    def test_interview_detail_view_not_found(self):
        """Test that an invalid interview id returns a 404 status code."""
        invalid_url = reverse("interview_detail", kwargs={"pk": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

