from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch

from tutorials.models.employer_models import Employer, Job
from tutorials.views.employer_views import employer_job_listings

User = get_user_model()

@override_settings(
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                (
                    'django.template.loaders.locmem.Loader',
                    {
                        'employer_job_listings.html': 'Dummy employer job listings template',
                        'error.html': 'Dummy error template: {{ message }}',
                        'log_in.html': 'Dummy login template'
                    }
                )
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }]
)
class EmployerJobListingsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an employer user.
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.employer_user)
        # Create an Employer instance with the same username as request.user.username.
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",  # must match request.user.username
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        # Create two Job instances for this employer.
        self.job1 = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job description 1"
        )
        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Data Scientist",
            description="Job description 2"
        )
        self.url = reverse("employer_job_listings")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        # The login URL is determined by your settings; here we assume reverse("log_in")
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_employer_not_found(self):
        """Test that if no Employer instance exists for the logged-in user, the error template is rendered."""
        # Delete the Employer instance.
        self.employer.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Check that the error template content is rendered.
        self.assertIn("Employer profile not found", response.content.decode())

    @patch("tutorials.views.employer_views.match_candidates_to_job")
    def test_employer_job_listings_with_matches(self, mock_match):
        """
        Test that when jobs exist, the view attaches matched_candidates.
        Simulate match_candidates_to_job returning a list of candidate-score tuples.
        """
        # Simulate a match function that returns a list of tuples.
        mock_match.return_value = [("candidate1", 0.85), ("candidate2", 0.75)]
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer_job_listings.html")
        jobs = response.context["jobs"]
        # There are two jobs.
        self.assertEqual(jobs.count(), 2)
        # For each job, matched_candidates should be the list from our patch.
        for job in jobs:
            self.assertEqual(job.matched_candidates, [("candidate1", 0.85), ("candidate2", 0.75)])
            mock_match.assert_any_call(job.title, top_n=5)

    @patch("tutorials.views.employer_views.match_candidates_to_job")
    def test_employer_job_listings_with_match_error(self, mock_match):
        """
        Test that if match_candidates_to_job returns an error message (string),
        the view attaches an empty list to matched_candidates.
        """
        mock_match.return_value = "No candidates found."
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        jobs = response.context["jobs"]
        for job in jobs:
            self.assertEqual(job.matched_candidates, [])

    def test_employer_job_listings_no_jobs(self):
        """Test that if the employer has no jobs, the view still renders with an empty jobs queryset."""
        Job.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        jobs = response.context["jobs"]
        self.assertEqual(jobs.count(), 0)
