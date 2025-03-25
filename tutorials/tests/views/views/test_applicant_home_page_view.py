# test_applicant_home_page_view.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from tutorials.models.applicants_models import Applicant
from tutorials.models.employer_models import Job

User = get_user_model()

class ApplicantHomePageViewTests(TestCase):
    def setUp(self):
        """
        Set up test data for applicant home page view
        """
        # ✅ Create a user who will be an applicant
        self.applicant_user = User.objects.create_user(
            username="test_applicant",
            password="password123",
            email="test_applicant@example.com"  # Provide unique email
        )
        # Make sure they have the correct role
        self.applicant_user.role = "Applicant"  
        self.applicant_user.save()

        self.applicant = Applicant.objects.create(user=self.applicant_user)

        # ✅ Create another user who is NOT an applicant (to test access control)
        self.non_applicant_user = User.objects.create_user(
            username="test_non_applicant",
            password="password123",
            email="test_non_applicant@example.com"  # Different unique email
        )
        # Give them a non-applicant role
        self.non_applicant_user.role = "Employer"
        self.non_applicant_user.save()

        # ✅ Create some test jobs (only 'approved' ones should show)
        self.approved_job_1 = Job.objects.create(
            title="Software Developer",
            company_name="TechStars",
            location="Gainesville, FL",
            salary=80000,
            job_type="Full Time",
            status="approved"
        )
        self.approved_job_2 = Job.objects.create(
            title="Data Analyst",
            company_name="DataCorp",
            location="Orlando, FL",
            salary=65000,
            job_type="Part Time",
            status="approved"
        )
        self.rejected_job = Job.objects.create(
            title="Intern",
            company_name="HiddenCo",
            location="Tampa, FL",
            salary=30000,
            job_type="Internship",
            status="rejected"
        )

        # ✅ Initialize Client for making requests
        self.client = Client()

    def test_redirect_if_not_logged_in(self):
        """
        Test that non-logged-in users are redirected to the login page
        """
        response = self.client.get(reverse("applicants-home-page"))
        self.assertRedirects(
            response,
            reverse("log-in") + "?next=" + reverse("applicants-home-page")
        )

    def test_access_denied_for_non_applicant(self):
        """
        Test that a logged-in user who is NOT an applicant cannot access the page
        The @applicant_only decorator typically would raise 403 or redirect.
        """
        self.client.login(username="test_non_applicant", password="password123")
        response = self.client.get(reverse("applicants-home-page"))
        self.assertEqual(response.status_code, 403)

    def test_home_page_loads_for_applicant(self):
        """
        Test if the applicant home page loads correctly for a valid applicant user
        """
        self.client.login(username="test_applicant", password="password123")
        response = self.client.get(reverse("applicants-home-page"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_home_page.html")

        # ✅ By default, only approved jobs should be displayed
        approved_jobs = response.context["approved_jobs"]
        self.assertEqual(len(approved_jobs), 2)
        self.assertIn(self.approved_job_1, approved_jobs)
        self.assertIn(self.approved_job_2, approved_jobs)
        self.assertNotIn(self.rejected_job, approved_jobs)

        # ✅ The template context should include these for filtering
        self.assertIn("companies", response.context)
        self.assertIn("locations", response.context)

    def test_location_filter(self):
        """
        Test that filtering by location returns only matching jobs
        """
        self.client.login(username="test_applicant", password="password123")

        response = self.client.get(reverse("applicants-home-page"), {"location": "Gainesville, FL"})
        self.assertEqual(response.status_code, 200)
        filtered_jobs = response.context["approved_jobs"]

        # Only the Gainesville job should remain
        self.assertEqual(len(filtered_jobs), 1)
        self.assertEqual(filtered_jobs[0].title, "Software Developer")

    def test_salary_filter(self):
        """
        Test that filtering by salary range returns only jobs within the specified interval
        """
        self.client.login(username="test_applicant", password="password123")

        response = self.client.get(reverse("applicants-home-page"), {"salary_interval": "0-70000"})
        self.assertEqual(response.status_code, 200)
        filtered_jobs = response.context["approved_jobs"]

        # Data Analyst (65,000) is within this range; Developer (80,000) is not
        self.assertEqual(len(filtered_jobs), 1)
        self.assertEqual(filtered_jobs[0].title, "Data Analyst")

    def test_job_type_filter(self):
        """
        Test that filtering by job type returns only matching jobs
        """
        self.client.login(username="test_applicant", password="password123")

        response = self.client.get(reverse("applicants-home-page"), {"job_type": "full-time"})
        self.assertEqual(response.status_code, 200)
        filtered_jobs = response.context["approved_jobs"]

        self.assertEqual(len(filtered_jobs), 1)
        self.assertEqual(filtered_jobs[0].title, "Software Developer")

    def test_company_filter(self):
        """
        Test that filtering by company returns only matching jobs
        """
        self.client.login(username="test_applicant", password="password123")

        response = self.client.get(reverse("applicants-home-page"), {"company": "TechStars"})
        self.assertEqual(response.status_code, 200)
        filtered_jobs = response.context["approved_jobs"]

        self.assertEqual(len(filtered_jobs), 1)
        self.assertEqual(filtered_jobs[0].company_name, "TechStars")

    def test_no_approved_jobs(self):
        """
        Test case when there are no approved jobs in the system
        """
        self.client.login(username="test_applicant", password="password123")
        Job.objects.filter(status="approved").delete()

        response = self.client.get(reverse("applicants-home-page"))
        self.assertEqual(response.status_code, 200)

        approved_jobs = response.context["approved_jobs"]
        self.assertEqual(len(approved_jobs), 0)
        # Confirm the empty message is shown
        self.assertContains(response, "No job matches your preferences")
