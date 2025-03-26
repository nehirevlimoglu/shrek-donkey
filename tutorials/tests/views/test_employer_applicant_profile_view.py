from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from tutorials.models.employer_models import Candidate, Interview, Job
from tutorials.models.applicants_models import Applicant, Application

User = get_user_model()

class ApplicantProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.login(username="applicantuser", password="password123")

        self.job = Job.objects.create(
            title="Test Job",
            description="Some job",
            application_deadline=timezone.now().date() + timezone.timedelta(days=7)
        )

        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            application_status="Pending"
        )

        self.applicant = Applicant.objects.create(user=self.user)

        self.application = Application.objects.create(
            applicant=self.applicant,
            job=self.job,
            work_experience=[{
                "work_start_date": "2022-01-01",
                "work_end_date": "2023-01-01"
            }]
        )

        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=timezone.now().date(),
            time=timezone.now().time()
        )

        self.url = reverse("applicant_profile", kwargs={"applicant_id": self.candidate.id})

    def test_profile_get_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicant_profile.html")
        self.assertEqual(response.context["candidate"], self.candidate)
        self.assertEqual(response.context["application"], self.application)
        self.assertEqual(response.context["latest_interview"], self.interview)

    def test_candidate_not_found(self):
        url = reverse("applicant_profile", kwargs={"applicant_id": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Candidate does not exist", response.content.decode())

    def test_applicant_not_found(self):
        self.applicant.delete()  # remove the matching Applicant
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Applicant profile not found", response.content.decode())

    def test_application_not_found(self):
        self.application.delete()  # remove Application
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["application"])

    def test_post_valid_status_change(self):
        data = {"status": "Hired"}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, "Hired")

    def test_post_invalid_status(self):
        data = {"status": "NotARealStatus"}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.candidate.refresh_from_db()
        # Should remain unchanged
        self.assertEqual(self.candidate.application_status, "Pending")
    
    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("log_in"), response.url)

