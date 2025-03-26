from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from tutorials.models.employer_models import Employer, Job, Candidate, Interview

User = get_user_model()

class AdminApplicationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpass",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)

        self.employer_user = User.objects.create_user(username="employer", email="employer@example.com", password="test", role="Employer")
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employer",
            email="employer@example.com",
            company_name="TestCo",
            company_location="City",
            industry="Tech"
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title="Developer",
            company_name="TestCo",
            location="Remote",
            description="Write code",
            application_deadline=timezone.now().date() + timedelta(days=10)
        )

        self.candidate_user = User.objects.create_user(username="candidate1", email="c1@example.com", password="test", role="Applicant")
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            job=self.job,
            application_status="Pending",
            application_date=timezone.now() - timedelta(days=1),
            first_name="Ali",
            last_name="Smith"
        )

        self.other_candidate = Candidate.objects.create(
            user=User.objects.create_user(username="candidate2", email="c2@example.com", password="test", role="Applicant"),
            job=self.job,
            application_status="Hired",
            application_date=timezone.now() - timedelta(days=2),
            first_name="Bob",
            last_name="Johnson"
        )

        self.rejected_candidate = Candidate.objects.create(
            user=User.objects.create_user(username="candidate3", email="c3@example.com", password="test", role="Applicant"),
            job=self.job,
            application_status="Rejected",
            application_date=timezone.now() - timedelta(days=3),
            first_name="Cara",
            last_name="Jones"
        )

        Interview.objects.create(candidate=self.candidate, job=self.job, date=timezone.now().date(), time=timezone.now().time())

        self.url = reverse("admin_applications_view")

    def test_view_renders_correct_template_and_context(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin_applications_view.html")
        self.assertIn("applications", response.context)
        self.assertEqual(response.context["total_applications"], 3)
        self.assertEqual(response.context["pending_applications"], 1)
        self.assertEqual(response.context["interview_applications"], 1)
        self.assertEqual(response.context["hired_applications"], 1)
        self.assertEqual(response.context["rejected_applications"], 1)

    def test_search_filter_matches_username(self):
        response = self.client.get(self.url, {"search": "candidate1"})
        self.assertEqual(response.status_code, 200)
        applications = response.context["applications"]
        self.assertEqual(applications.paginator.count, 1)

    def test_status_filter_hired(self):
        response = self.client.get(self.url, {"status": "Hired"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["applications"].paginator.count, 1)

    def test_combined_search_and_status_filter(self):
        response = self.client.get(self.url, {"search": "candidate2", "status": "Hired"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["applications"].paginator.count, 1)

    def test_status_filter_all_does_not_filter(self):
        response = self.client.get(self.url, {"status": "all"})
        self.assertEqual(response.context["applications"].paginator.count, 3)

    def test_application_ordering_descending(self):
        response = self.client.get(self.url)
        apps = list(response.context["applications"].object_list)
        dates = [a.application_date for a in apps]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_pagination_page_1(self):
        response = self.client.get(self.url, {"page": 1})
        self.assertEqual(response.context["applications"].number, 1)

    def test_pagination_non_integer(self):
        response = self.client.get(self.url, {"page": "notanumber"})
        self.assertEqual(response.context["applications"].number, 1)

    def test_pagination_empty_page(self):
        response = self.client.get(self.url, {"page": 999})
        paginator = response.context["applications"]
        self.assertEqual(paginator.number, paginator.paginator.num_pages)

    def test_redirect_for_non_admin(self):
        self.client.logout()
        normal_user = User.objects.create_user(username="regular", email="r@e.com", password="pass", role="Applicant")
        self.client.force_login(normal_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
