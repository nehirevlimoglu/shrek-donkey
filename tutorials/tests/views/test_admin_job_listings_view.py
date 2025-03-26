from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job, Candidate, Employer, EmployerNotification
# Adjust this import if your Admin model is in a different module.
from tutorials.models.admin_models import Admin

User = get_user_model()

class AdminJobListingsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        
        # Create an admin user (role "Admin")
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin"
        )
        
        # Create an Admin instance using the admin_user
        self.admin_instance = Admin.objects.create(
            user=self.admin_user,
            username="adminuser_admin",
            email="admin_admin@example.com"
        )
    
    # ... rest of your setUp code ...

        
        # For testing, create some jobs:
        # Open job (deadline in future)
        self.open_job1 = Job.objects.create(
            title="Open Job 1",
            company_name="Company A",
            application_deadline=self.today + timedelta(days=5),
            created_at=timezone.now()
        )
        # Open job (deadline is None)
        self.open_job2 = Job.objects.create(
            title="Open Job 2",
            company_name="Company B",
            application_deadline=None,
            created_at=timezone.now() - timedelta(days=1)
        )
        # Closed job (deadline in past)
        self.closed_job = Job.objects.create(
            title="Closed Job",
            company_name="Company C",
            application_deadline=self.today - timedelta(days=1),
            created_at=timezone.now() - timedelta(days=2)
        )
        
        # Create some candidate applications
        # Candidate for open_job1
        Candidate.objects.create(
            user=self.admin_user,  # For simplicity, using admin_user as candidate
            job=self.open_job1,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="Admin",
            last_name="User"
        )
        # Candidate for closed_job
        Candidate.objects.create(
            user=self.admin_user,
            job=self.closed_job,
            application_status="Hired",
            application_date=timezone.now(),
            first_name="Admin",
            last_name="User"
        )
        
        # Create a test notification for context (if needed)
        # (This may be used by your view to display notifications.)
        self.notification = EmployerNotification.objects.create(
            employer=Employer.objects.create(
                user=self.admin_user,
                username="test_employer",
                email="employer@example.com",
                company_name="Tech Corp",
                company_location="New York",
                industry="Tech"
            ),
            title="New Application",
            message="An applicant applied."
        )

        # Log in as admin user
        self.client.login(username="adminuser", password="password123")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users cannot access the admin job listings page."""
        self.client.logout()
        response = self.client.get(reverse("admin_job_listings"))
        expected_redirect = reverse("log_in") + "?next=" + reverse("admin_job_listings")
        self.assertRedirects(response, expected_redirect)

    def test_search_filter(self):
        """Test that search filtering works correctly."""
        # Search for a term present in an open job's title
        response = self.client.get(reverse("admin_job_listings"), {"search": "Open Job 1"})
        self.assertEqual(response.status_code, 200)
        jobs = response.context["jobs"]
        # Every returned job should have "Open Job 1" (case-insensitive) in its title or company name.
        for job in jobs:
            self.assertTrue("open job 1" in job.title.lower() or "open job 1" in job.company_name.lower())

    def test_status_filter_open(self):
        """Test that status filter 'open' returns only open jobs."""
        response = self.client.get(reverse("admin_job_listings"), {"status": "open"})
        self.assertEqual(response.status_code, 200)
        jobs = response.context["jobs"]
        # All returned jobs should be open.
        for job in jobs:
            self.assertEqual(job.status, "Open")

    def test_status_filter_closed(self):
        """Test that status filter 'closed' returns only closed jobs."""
        response = self.client.get(reverse("admin_job_listings"), {"status": "closed"})
        self.assertEqual(response.status_code, 200)
        jobs = response.context["jobs"]
        for job in jobs:
            self.assertEqual(job.status, "Closed")

    def test_pagination(self):
        """Test that pagination returns 5 jobs per page."""
        # Create additional jobs so we have more than 5.
        for i in range(10):
            Job.objects.create(
                title=f"Job {i}",
                company_name="Test Co",
                application_deadline=self.today + timedelta(days=10),
                created_at=timezone.now() - timedelta(days=i)
            )
        response = self.client.get(reverse("admin_job_listings"))
        jobs_page = response.context["jobs"]
        # Check that we have at most 5 jobs on the current page.
        self.assertLessEqual(len(jobs_page.object_list), 5)

    def test_context_statistics(self):
        """Test that context statistics are correctly calculated."""
        response = self.client.get(reverse("admin_job_listings"))
        total_jobs = Job.objects.count()
        open_jobs = Job.objects.filter(Q(application_deadline__isnull=True) | Q(application_deadline__gt=self.today)).count()
        closed_jobs = total_jobs - open_jobs

        self.assertEqual(response.context["total_jobs"], total_jobs)
        self.assertEqual(response.context["open_jobs"], open_jobs)
        self.assertEqual(response.context["closed_jobs"], closed_jobs)
