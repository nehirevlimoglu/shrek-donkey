from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer, Job
from datetime import date, timedelta

User = get_user_model()

class JobDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create a test user and employer
        self.user = User.objects.create_user(
            username="@damla", email="damla@example.org",
            password="Password123", role="Employer"
        )
        self.employer = Employer.objects.create(
            user=self.user,
            username="@damla",
            email="damla@example.org",
            company_name="Damla Corp",
            company_location="London",
            industry="Tech"
        )

        # Create a test job
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            company_name="Damla Corp",
            location="Remote",
            job_type="Full Time",
            salary=80000,
            description="Exciting role in a fast-paced team.",
            requirements="Python, Django",
            benefits="Remote work, 401k",
            application_deadline=date.today() + timedelta(days=10),
            contact_email="jobs@damlacorp.com"
        )

    def test_job_detail_view_returns_200(self):
        url = reverse("employer_job_detail", kwargs={"job_id": self.job.id})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "job_detail.html")
        self.assertContains(response, "Software Engineer")
        self.assertEqual(response.context["job"].id, self.job.id)

    def test_job_detail_404_if_invalid_id(self):
        url = reverse("employer_job_detail", kwargs={"job_id": 9999})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
