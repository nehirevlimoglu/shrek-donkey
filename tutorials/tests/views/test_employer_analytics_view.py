from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer, Job, Candidate, Interview

User = get_user_model()

class EmployerAnalyticsViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # ✅ Create employer user and employer profile
        self.user = User.objects.create_user(
            username="@damla",
            password="Password123",
            role="Employer",
            email="damla@example.org",
            first_name="Damla",
            last_name="Sen"
        )

        self.employer = Employer.objects.create(
            user=self.user,
            username="@damla",
            email=self.user.email,
            company_name="Damla Sen Corp",
            company_location="London",
            industry="Tech",
            company_size=50,
            account_status="Active",
            subscription_plan="Free",
            is_verified=True
        )

        # ✅ Create jobs for employer
        self.job1 = Job.objects.create(
            employer=self.employer,
            title="Backend Developer",
            application_deadline=now().date() + timedelta(days=10),
            description="Build APIs."
        )

        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Frontend Developer",
            application_deadline=now().date() + timedelta(days=15),
            description="Build UIs."
        )

        # ✅ Create applicant user
        self.applicant = User.objects.create_user(
            username="@rares",
            password="Password123",
            role="Applicant",
            email="rares@example.org"
        )

        Candidate.objects.create(
            user=self.applicant,
            job=self.job1,
            application_date=now(),
            application_status="Hired"
        )

        Candidate.objects.create(
            user=self.applicant,
            job=self.job2,
            application_date=now()
        )

        Interview.objects.create(
            job=self.job1,
            date=now().date() + timedelta(days=2),
            candidate=Candidate.objects.filter(job=self.job1).first(),
            time=now().time(),
            interview_link="https://zoom.us/fake-interview"
        )

        self.client.login(username="@damla", password="Password123")

    def test_analytics_view_status_code(self):
        response = self.client.get(reverse("employer_analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer_analytics.html")

    def test_analytics_context_data(self):
        response = self.client.get(reverse("employer_analytics"))
        self.assertEqual(response.context["total_jobs"], 2)
        self.assertEqual(response.context["total_applicants"], 2)
        self.assertEqual(response.context["pending_interviews"], 1)
        self.assertEqual(response.context["average_apps_per_job"], 1.0)
        self.assertEqual(len(response.context["job_analytics"]), 2)

    def test_job_titles_json(self):
        response = self.client.get(reverse("employer_analytics"))
        self.assertIn("Backend Developer", response.context["job_titles"])
        self.assertIn("Frontend Developer", response.context["job_titles"])

    def test_applicants_and_interviews_serialized(self):
        response = self.client.get(reverse("employer_analytics"))
        self.assertIn("job_applicants", response.context)
        self.assertIn("job_interviews", response.context)

