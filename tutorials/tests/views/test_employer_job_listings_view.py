from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from tutorials.models.employer_models import Employer, Job

User = get_user_model()

class EmployerJobListingsViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # ✅ Create employer user
        self.user = User.objects.create_user(
            username="@damla",
            password="Password123",
            role="Employer",
            email="damla@example.org"
        )

        # ✅ Employer profile
        self.employer = Employer.objects.create(
            user=self.user,
            username="@damla",
            email=self.user.email,
            company_name="Damla Inc",
            company_location="London",
            industry="Tech",
            is_verified=True
        )

        # ✅ Create jobs for this employer
        self.job1 = Job.objects.create(
            employer=self.employer,
            title="Backend Engineer",
            application_deadline=now().date() + timedelta(days=7),
            description="Build REST APIs."
        )
        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Frontend Developer",
            application_deadline=now().date() + timedelta(days=14),
            description="Build frontend apps."
        )

        # ✅ Login the employer
        self.client.login(username="@damla", password="Password123")

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse("employer_job_listings"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("log_in"), response.url)

    def test_job_listings_visible_to_employer(self):
        response = self.client.get(reverse("employer_job_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer_job_listings.html")

        jobs = response.context["jobs"]
        self.assertEqual(len(jobs), 2)
        self.assertIn(self.job1, jobs)
        self.assertIn(self.job2, jobs)

    def test_employer_with_no_jobs(self):
        Job.objects.all().delete()
        response = self.client.get(reverse("employer_job_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["jobs"]), 0)
