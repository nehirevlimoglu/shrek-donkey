from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta

from tutorials.models.employer_models import Job, Employer
from tutorials.models.applicants_models import Applicant, Application
from tutorials.forms.applicants_forms import ApplicationForm

User = get_user_model()

class ApplicantsApplicationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.applicant_user)

        self.applicant_obj = Applicant.objects.create(user=self.applicant_user)

        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Co",
            company_location="Test City",
            industry="Tech"
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Developer",
            description="Exciting role",
            application_deadline=self.today + timedelta(days=10)
        )

        self.url = reverse("applicants_application", kwargs={"job_id": self.job.id})

    def test_get_application_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_application.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], ApplicationForm)

    def test_redirect_if_already_applied(self):
        Application.objects.create(
            applicant=self.applicant_obj,
            job=self.job,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            address="123 Main St",
            education=[],
            work_experience=[],
            current_job_title="Dev",
            current_employer="Company X",
            how_did_you_hear="linkedin",
            sponsorship_needed="no",
            confirm_information=True,
            status="under_review"
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("job_detail", kwargs={"job_id": self.job.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already applied" in m.message for m in messages))

    def test_post_valid_application(self):
        resume_file = SimpleUploadedFile("resume.pdf", b"dummy", content_type="application/pdf")
        valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "resume": resume_file,
            "current_job_title": "Engineer",
            "current_employer": "Test Inc",
            "linkedin_profile": "",
            "portfolio_website": "",
            "how_did_you_hear": "linkedin",
            "sponsorship_needed": "no",
            "confirm_information": "on",
            "school[]": ["Uni A"],
            "degree[]": ["BSc"],
            "discipline[]": ["CS"],
            "start_date[]": ["2015-01-01"],
            "end_date[]": ["2019-01-01"],
            "work_job_title[]": ["Dev"],
            "work_employer[]": ["Work Co"],
            "work_start_date[]": ["2020-01-01"],
            "work_end_date[]": ["2022-01-01"],
            "job_description[]": ["Did stuff"]
        }
        response = self.client.post(self.url, valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("job_detail", kwargs={"job_id": self.job.id}))
        application = Application.objects.get(applicant=self.applicant_obj, job=self.job)
        self.assertEqual(application.education[0]["school"], "Uni A")
        self.assertEqual(application.work_experience[0]["work_employer"], "Work Co")

    def test_post_invalid_application(self):
        invalid_data = {"first_name": "", "resume": SimpleUploadedFile("resume.pdf", b"", content_type="application/pdf")}
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_application.html")
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertTrue(form.errors)

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        expected_url = reverse("log_in") + f"?next={self.url}"
        self.assertRedirects(response, expected_url)
