from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer, Job, Candidate, EmployerNotification

User = get_user_model()  # ✅ Use the correct user model

class EmployerHomePageViewTests(TestCase):

    def setUp(self):
        """Set up test data for employer home page view"""

        # ✅ Create a User instance with a unique email
        self.user = User.objects.create_user(
            username="test_employer",
            email="employer@example.com",  # unique email
            password="password123"
        )

        # ✅ Link the User to Employer instance
        self.employer = Employer.objects.create(
            user=self.user,
            username="test_employer",
            email="employer@example.com",  # same email as user is fine here
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )

        # ✅ Create test job listings (one active, one expired)
        self.active_job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            application_deadline=now().date() + timedelta(days=10),
            description="Looking for a great developer!"
        )
        self.expired_job = Job.objects.create(
            employer=self.employer,
            title="Expired Job",
            application_deadline=now().date() - timedelta(days=1),
            description="This job is expired."
        )

        # ✅ Create test applicant with a UNIQUE email
        self.applicant_user = User.objects.create_user(
            username="test_applicant",
            email="applicant@example.com",  # unique email!
            password="password123"
        )
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.active_job,
            application_date=now(),
            first_name="John",
            last_name="Doe"
        )

        # ✅ Create test notification
        self.notification = EmployerNotification.objects.create(
            employer=self.employer,
            title="New Application",
            message="An applicant applied."
        )

        # ✅ Client for making requests
        self.client = Client()



    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users cannot access the page"""
        response = self.client.get(reverse("employer_home_page"))
        self.assertRedirects(response, reverse("log_in") + "?next=" + reverse("employer_home_page"))

    def test_error_if_employer_not_found(self):
        """Test if view handles employer not found case"""
        Employer.objects.all().delete()  # ✅ Remove employer to trigger error
        self.client.login(username="test_employer", password="password123")
        response = self.client.get(reverse("employer_home_page"))
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {"success": False, "error": "Employer profile not found"})

    def test_successful_dashboard_load(self):
        """Test if the employer dashboard loads correctly"""
        self.client.login(username="test_employer", password="password123")
        response = self.client.get(reverse("employer_home_page"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employers_home_page.html")

        # ✅ Test total job count
        self.assertEqual(response.context["total_jobs"], 2)

        # ✅ Test active listings count
        self.assertEqual(response.context["active_listings"], 1)

        # ✅ Test total applicants count
        self.assertEqual(response.context["total_applicants"], 1)

        # ✅ Test recent applicants (should only include those for this employer)
        self.assertEqual(len(response.context["recent_applicants"]), 1)
        self.assertEqual(response.context["recent_applicants"][0].user.username, "test_applicant")

        # ✅ Test notifications exist
        self.assertEqual(len(response.context["notifications"]), 1)
        self.assertEqual(response.context["notifications"][0].title, "New Application")

    def test_no_applicants_no_jobs(self):
        """Test case when employer has no jobs or applicants"""
        self.client.login(username="test_employer", password="password123")

        # Delete all jobs and candidates
        Job.objects.all().delete()
        Candidate.objects.all().delete()

        response = self.client.get(reverse("employer_home_page"))

        # ✅ Test zero jobs, active listings, and applicants
        self.assertEqual(response.context["total_jobs"], 0)
        self.assertEqual(response.context["active_listings"], 0)
        self.assertEqual(response.context["total_applicants"], 0)

