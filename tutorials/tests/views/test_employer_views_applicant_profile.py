from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import Candidate, Job, Interview
from datetime import timedelta

User = get_user_model()

class ApplicantProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.user)

        self.job = Job.objects.create(
            title="Test Job",
            description="Test Description",
            application_deadline=timezone.now().date() + timedelta(days=7)
        )

        self.applicant = Applicant.objects.create(user=self.user)

        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            first_name="Jane",
            last_name="Doe",
            application_status="Pending"
        )

        self.application = Application.objects.create(
            applicant=self.applicant,
            job=self.job
        )

        self.url = reverse("applicant_profile", kwargs={"applicant_id": self.candidate.id})

    def test_candidate_not_found(self):
        response = self.client.get(reverse("applicant_profile", kwargs={"applicant_id": 999}))
        self.assertEqual(response.status_code, 404)
        self.assertIn("Candidate does not exist.", response.content.decode())

    def test_applicant_profile_not_found(self):
        self.applicant.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Applicant profile not found.", response.content.decode())

    def test_application_not_found(self):
        self.application.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("candidate", response.context)
        self.assertIsNone(response.context.get("application"))

    def test_post_valid_status_update(self):
        response = self.client.post(self.url, {"status": "Hired"})
        self.assertRedirects(response, self.url)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, "Hired")

    def test_post_invalid_status_update(self):
        response = self.client.post(self.url, {"status": "InvalidStatus"})
        self.assertRedirects(response, self.url)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, "Pending")

    def test_work_experience_duration_computed(self):
        self.application.work_experience = [{
            "work_start_date": "2020-01-01",
            "work_end_date": "2021-01-01",
            "work_employer": "ABC Corp"
        }]
        self.application.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("duration", response.context["application"].work_experience[0])

    def test_interview_shown(self):
        Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=timezone.now().date(),
            time=timezone.now().time()
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("latest_interview", response.context)

    def test_render_get_view_successfully(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicant_profile.html")
        self.assertEqual(response.context["candidate"], self.candidate)