from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Candidate, Job, Employer

User = get_user_model()

class AdminApplicationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        # Create an admin user with necessary flags so that is_admin passes.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)

        # Create an employer (if needed by the view)
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )

        # Create some jobs for candidates to apply to.
        self.job1 = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            company_name="Tech Corp",
            application_deadline=self.today + timedelta(days=10),
            description="Job description 1"
        )
        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Data Scientist",
            company_name="Tech Corp",
            application_deadline=self.today + timedelta(days=20),
            description="Job description 2"
        )

        # Create several candidate applications with different statuses.
        # We'll create 1 candidate for each status.
        self.candidate_pending = Candidate.objects.create(
            user=self.admin_user,  # Using admin user for testing (simplification)
            job=self.job1,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )
        self.candidate_interview = Candidate.objects.create(
            user=self.admin_user,
            job=self.job1,
            application_status="Interview",
            application_date=timezone.now() - timedelta(days=1),
            first_name="Alice",
            last_name="Smith"
        )
        self.candidate_hired = Candidate.objects.create(
            user=self.admin_user,
            job=self.job2,
            application_status="Hired",
            application_date=timezone.now() - timedelta(days=2),
            first_name="Bob",
            last_name="Brown"
        )
        self.candidate_rejected = Candidate.objects.create(
            user=self.admin_user,
            job=self.job2,
            application_status="Rejected",
            application_date=timezone.now() - timedelta(days=3),
            first_name="Carol",
            last_name="White"
        )

        self.url = reverse("admin_applications_view")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_search_filter(self):
        """Test that the search filter returns applications matching the search query."""
        # Search by candidate's first name
        response = self.client.get(self.url, {"search": "Alice"})
        self.assertEqual(response.status_code, 200)
        applications = response.context["applications"].object_list
        self.assertTrue(any("alice" in app.user.first_name.lower() for app in applications)
                        or any("alice" in app.user.username.lower() for app in applications)
                        or any("alice" in app.job.title.lower() for app in applications)
                        or any("alice" in app.job.company_name.lower() for app in applications))
    
    def test_status_filter(self):
        """Test that filtering by application_status returns only matching applications."""
        response = self.client.get(self.url, {"status": "Pending"})
        self.assertEqual(response.status_code, 200)
        applications = response.context["applications"].object_list
        for app in applications:
            self.assertEqual(app.application_status, "Pending")
    
    def test_pagination(self):
        """Test that pagination limits the applications to 5 per page."""
        # Create additional candidate applications to exceed 5
        for i in range(6):
            Candidate.objects.create(
                user=self.admin_user,
                job=self.job1,
                application_status="Pending",
                application_date=timezone.now() - timedelta(days=i),
                first_name=f"Extra{i}",
                last_name="User"
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        applications_page = response.context["applications"]
        # Check that the number of applications on the page is <= 5.
        self.assertLessEqual(len(applications_page.object_list), 5)

    def test_context_statistics(self):
        """Test that context statistics for applications are calculated correctly."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        total_applications = Candidate.objects.count()
        pending_applications = Candidate.objects.filter(application_status="Pending").count()
        interview_applications = Candidate.objects.filter(application_status="Interview").count()
        hired_applications = Candidate.objects.filter(application_status="Hired").count()
        rejected_applications = Candidate.objects.filter(application_status="Rejected").count()

        self.assertEqual(response.context["total_applications"], total_applications)
        self.assertEqual(response.context["pending_applications"], pending_applications)
        self.assertEqual(response.context["interview_applications"], interview_applications)
        self.assertEqual(response.context["hired_applications"], hired_applications)
        self.assertEqual(response.context["rejected_applications"], rejected_applications)
