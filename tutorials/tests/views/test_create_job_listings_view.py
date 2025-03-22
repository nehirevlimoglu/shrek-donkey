from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from tutorials.models.employer_models import Employer, Job
from tutorials.forms.employer_forms import JobForm

User = get_user_model()

class CreateJobListingViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # ✅ Create employer user and profile
        self.user = User.objects.create_user(
            username="@damla",
            password="Password123",
            role="Employer",
            email="damla@example.org",
        )
        self.employer = Employer.objects.create(
            user=self.user,
            username=self.user.username,
            email=self.user.email,
            company_name="Damla Corp",
            company_location="London",
            industry="Tech"
        )
        self.client.login(username="@damla", password="Password123")

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse("create_job_listings"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("log_in"), response.url)

    def test_redirect_if_employer_profile_missing(self):
        self.employer.delete()
        response = self.client.get(reverse("create_job_listings"), follow=True)
        self.assertRedirects(response, reverse("employer_home_page"), status_code=302, target_status_code=403)


    def test_get_request_renders_form(self):
        response = self.client.get(reverse("create_job_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer_create_job_listing.html")
        self.assertIsInstance(response.context["form"], JobForm)

    def test_valid_post_creates_job(self):
        form_data = {
            "title": "Software Engineer",
            "position": "Developer",
            "job_type": "Full Time",
            "salary": 80000,
            "description": "Looking for a talented developer.",
            "requirements": "Python, Django",
            "benefits": "Health insurance, 401k",
            "application_deadline": (now().date() + timedelta(days=10)).isoformat(),
            "location": "London",
            "company_name": "Damla Corp",
            "contact_email": "damla@example.org",  # ✅ Include it since it's required
        }

        # POST without follow so we stay on the form page if there's an error
        response = self.client.post(reverse("create_job_listings"), form_data, follow=False)

        # Print form errors safely (if any)
        if response.context and "form" in response.context:
            print("Form errors:", response.context["form"].errors)

        # Assert redirect happened
        self.assertEqual(response.status_code, 302)

        # Follow the redirect to the job listings page to verify job exists
        self.assertTrue(Job.objects.filter(title="Software Engineer").exists())

        job = Job.objects.get(title="Software Engineer")
        self.assertEqual(job.employer, self.employer)
        self.assertEqual(job.company_name, "Damla Corp")
        self.assertEqual(job.location, "London")
        self.assertEqual(job.contact_email, "damla@example.org")
        self.assertEqual(job.salary, 80000)
        self.assertEqual(job.job_type, "Full Time")





    def test_invalid_post_shows_error(self):
        # Missing required fields like title
        response = self.client.post(reverse("create_job_listings"), data={}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There was an error with your submission.")
