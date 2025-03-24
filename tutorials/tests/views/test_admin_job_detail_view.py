from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job, Candidate, Employer
# Import your admin check if needed (e.g., is_admin) for clarity, though not directly used here.
# from tutorials.views.admin_views import is_admin

User = get_user_model()

class AdminJobDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        # Create an admin user (make sure it passes is_admin check).
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

        # Create a job (we'll adjust its deadline and status in different tests)
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="This is a test job.",
            application_deadline=self.today + timedelta(days=5),  # future deadline by default
            status="active",  # assume "active" means not rejected
            created_at=timezone.now()
        )
        # Create a candidate for the job
        self.candidate = Candidate.objects.create(
            user=self.admin_user,  # for testing, using admin user as candidate
            job=self.job,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="Admin",
            last_name="User"
        )
        # Set the URL for the job detail view.
        self.url = reverse("admin_job_detail", kwargs={"job_id": self.job.id})

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_non_admin_user_redirected(self):
        """Test that a logged-in user without admin role is redirected."""
        # Create a non-admin user.
        non_admin = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(non_admin)
        response = self.client.get(self.url)
        # The decorator should redirect non-admin users.
        self.assertEqual(response.status_code, 302)

    def test_job_detail_open_with_future_deadline(self):
        """Test that a job with a future deadline is marked as open."""
        # Ensure the job's deadline is in the future.
        self.job.application_deadline = self.today + timedelta(days=5)
        self.job.status = "active"
        self.job.save()
        response = self.client.get(self.url)
        # Refresh the job instance from context.
        job = response.context["job"]
        self.assertTrue(job.is_open)
        self.assertEqual(job.display_status, "Open")
        # Also, candidate_count should match.
        self.assertEqual(response.context["candidate_count"], Candidate.objects.filter(job=self.job).count())

    def test_job_detail_closed_due_to_deadline(self):
        """Test that a job with a deadline in the past (or today) is marked as closed."""
        self.job.application_deadline = self.today  # deadline is today (or in the past)
        self.job.status = "active"
        self.job.save()
        response = self.client.get(self.url)
        job = response.context["job"]
        self.assertFalse(job.is_open)
        self.assertEqual(job.display_status, "Closed")

    def test_job_detail_closed_due_to_rejected_status(self):
        """Test that a job with no deadline but with status 'rejected' is marked as closed."""
        self.job.application_deadline = None
        self.job.status = "rejected"
        self.job.save()
        response = self.client.get(self.url)
        job = response.context["job"]
        self.assertFalse(job.is_open)
        self.assertEqual(job.display_status, "Closed")

    def test_job_detail_open_no_deadline_not_rejected(self):
        """Test that a job with no deadline and not rejected is marked as open."""
        self.job.application_deadline = None
        self.job.status = "active"
        self.job.save()
        response = self.client.get(self.url)
        job = response.context["job"]
        self.assertTrue(job.is_open)
        self.assertEqual(job.display_status, "Open")
