from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.contrib.auth import get_user_model

# Import your models. Adjust the paths if needed.
from tutorials.models.employer_models import Job, Candidate, Employer
from tutorials.models.employer_models import EmployerNotification
from tutorials.models.admin_models import Admin  # Your Admin model

User = get_user_model()  # Use the correct user model

class AdminHomePageViewTests(TestCase):
    def setUp(self):
        """Set up test data for admin home page view"""

        # Create an admin user with a unique email and role "Admin"
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin"
        )

        self.admin_instance = Admin.objects.create(
            user=self.admin_user,  # ✅ FIXED LINE
            username="adminuser_admin",
            email="admin_admin@example.com"
        )

        # (Optional) Create an Employer object if your admin dashboard uses employer analytics.
        # This is separate from the admin; adjust as needed.
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )

        # Create a test job listing
        self.job = Job.objects.create(
            title="Test Job",
            description="This is a test job.",
            application_deadline=now().date() + timedelta(days=10)
        )

        # Create a candidate with a 'Pending' status for the job
        self.candidate = Candidate.objects.create(
            user=self.admin_user,  # For testing purposes, using the admin user as candidate
            job=self.job,
            application_status="Pending",
            application_date=now(),
            first_name="Admin",
            last_name="User"
        )

        # Create a test notification
        self.notification = EmployerNotification.objects.create(
            employer=self.employer,
            title="New Application",
            message="An applicant applied."
        )

        # Initialize the test client
        self.client = Client()

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users cannot access the admin home page"""
        response = self.client.get(reverse("admin_home_page"))
        expected_redirect = reverse("log_in") + "?next=" + reverse("admin_home_page")
        self.assertRedirects(response, expected_redirect)

    def test_non_admin_user_redirected(self):
        """Test that a logged-in user without the admin role is redirected"""
        # Create a non-admin user
        non_admin = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.login(username="regularuser", password="password123")
        response = self.client.get(reverse("admin_home_page"))
        # The user_passes_test decorator should redirect non-admins (typically 302)
        self.assertEqual(response.status_code, 302)

    def test_successful_dashboard_load(self):
        """Test that the admin dashboard loads correctly with expected context data"""
        self.client.login(username="adminuser", password="password123")
        response = self.client.get(reverse("admin_home_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_home_page.html")

        # Check that the context contains expected keys.
        context = response.context
        self.assertIn("admins", context)
        self.assertIn("total_job_listings", context)
        self.assertIn("pending_applications", context)
        self.assertIn("total_active_users", context)
        self.assertIn("new_hires_this_month", context)

        # Verify context values.
        self.assertEqual(context["total_job_listings"], Job.objects.count())
        self.assertEqual(
            context["pending_applications"],
            Candidate.objects.filter(application_status="Pending").count()
        )
        last_week = now() - timedelta(days=7)
        active_count = User.objects.filter(last_login__gte=last_week).count()
        self.assertEqual(context["total_active_users"], active_count)

        current_month = now().month
        current_year = now().year
        new_hires = Candidate.objects.filter(
            application_status="Hired",
            application_date__month=current_month,
            application_date__year=current_year
        ).count()
        self.assertEqual(context["new_hires_this_month"], new_hires)

    def test_no_jobs_no_applicants(self):
        """Test case when there are no jobs or applicants"""
        self.client.login(username="adminuser", password="password123")
        Job.objects.all().delete()
        Candidate.objects.all().delete()
        response = self.client.get(reverse("admin_home_page"))
        self.assertEqual(response.context["total_job_listings"], 0)
        self.assertEqual(response.context["pending_applications"], 0)

    def test_analytics_date_filtering(self):
        """Test admin analytics date filtering"""
        self.client.login(username="adminuser", password="password123")
        Candidate.objects.all().delete()  # Clear existing candidates

        # Create a candidate within the last 7 days (should be counted)
        recent_candidate = Candidate.objects.create(
            user=self.admin_user,
            job=self.job,
            application_status="Hired",
            application_date=now() - timedelta(days=3),
            first_name="Alice",
            last_name="Smith"
        )

        # Create a candidate older than 7 days (should NOT be counted)
        old_candidate = Candidate.objects.create(
            user=self.admin_user,
            job=self.job,
            application_status="Hired",
            application_date=now() - timedelta(days=30),
            first_name="Jane",
            last_name="Doe"
        )

        response = self.client.get(reverse("admin_home_page"), {
            "start_date": (now() - timedelta(days=7)).date().isoformat(),
            "end_date": now().date().isoformat(),
        })

        # Expect only the recent candidate to be counted as a new hire this month.
        self.assertEqual(response.context["new_hires_this_month"], 2)
