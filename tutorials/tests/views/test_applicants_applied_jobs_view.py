from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Import models; adjust the import paths based on your project structure.
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import Job, Employer

User = get_user_model()

class ApplicantsAppliedJobsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        # Create an applicant user.
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.applicant_user)
        
        # Create an Applicant profile.
        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            # Add additional fields if required.
        )
        
        # Create an employer and job (needed for applications).
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
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        self.job1 = Job.objects.create(
            employer=self.employer,
            title="Job 1",
            description="Description for Job 1",
            application_deadline=self.today + timedelta(days=10)
        )
        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Job 2",
            description="Description for Job 2",
            application_deadline=self.today + timedelta(days=15)
        )
        # Create two Application instances for this applicant.
        self.application1 = Application.objects.create(
            applicant=self.applicant,
            job=self.job1,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            address="123 Main St",
            education=[],
            work_experience=[],
            current_job_title="Developer",
            current_employer="Some Company",
            linkedin_profile="",
            portfolio_website="",
            how_did_you_hear="other",
            sponsorship_needed="no",
            confirm_information=True,
            status="under_review"
        )
        self.application2 = Application.objects.create(
            applicant=self.applicant,
            job=self.job2,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            address="123 Main St",
            education=[],
            work_experience=[],
            current_job_title="Developer",
            current_employer="Some Company",
            linkedin_profile="",
            portfolio_website="",
            how_did_you_hear="other",
            sponsorship_needed="no",
            confirm_information=True,
            status="under_review"
        )
        # Build the URL using the correct reverse name.
        self.url = reverse("applicants-applied-jobs")

    def test_get_applied_jobs_success(self):
        """Test that a GET request returns the applied jobs for the logged-in applicant."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_applied_jobs.html")
        self.assertIn("applied_jobs", response.context)
        applied_jobs = response.context["applied_jobs"]
        self.assertEqual(applied_jobs.count(), 2)
        # Verify that the job titles match.
        job_titles = set(app.job.title for app in applied_jobs)
        self.assertEqual(job_titles, {"Job 1", "Job 2"})

    def test_no_applied_jobs(self):
        """Test that if the applicant has no applications, an empty queryset is returned."""
        Application.objects.filter(applicant=self.applicant).delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        applied_jobs = response.context["applied_jobs"]
        self.assertEqual(applied_jobs.count(), 0)

    def test_applicant_not_found(self):
        """Test that if no Applicant profile exists for the user, a 404 is raised."""
        self.applicant.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)