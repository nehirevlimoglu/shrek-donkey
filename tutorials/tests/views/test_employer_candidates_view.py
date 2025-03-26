from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Employer, Job, Candidate

User = get_user_model()

class EmployerCandidatesViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an employer user with role "Employer"
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.employer_user)
        
        # Create an Employer instance linked to the employer user.
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        
        # Create two jobs posted by this employer.
        self.job1 = Job.objects.create(
            employer=self.employer,
            title="Job 1",
            description="Description for Job 1",
            application_deadline=timezone.now().date() + timedelta(days=10)
        )
        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Job 2",
            description="Description for Job 2",
            application_deadline=timezone.now().date() + timedelta(days=15)
        )
        
        # Create candidate users (applicants) with discipline information.
        self.candidate_user1 = User.objects.create_user(
            username="candidate1",
            email="cand1@example.com",
            password="password123",
            role="Applicant"
        )
        self.candidate_user2 = User.objects.create_user(
            username="candidate2",
            email="cand2@example.com",
            password="password123",
            role="Applicant"
        )
        
        # Create Candidate objects for these jobs.
        self.candidate1 = Candidate.objects.create(
            user=self.candidate_user1,
            job=self.job1,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="Alice",
            last_name="Smith",
            discipline="bachelors"  # Lowercase discipline
        )
        self.candidate2 = Candidate.objects.create(
            user=self.candidate_user2,
            job=self.job2,
            application_status="Hired",
            application_date=timezone.now(),
            first_name="Bob",
            last_name="Jones",
            discipline="masters"  # Lowercase discipline
        )
        
        self.url = reverse("employer_candidates")
        
    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
        
    def test_forbidden_if_not_employer(self):
        """Test that a logged-in user without an Employer profile is forbidden."""
        # Create a non-employer user.
        non_employer = User.objects.create_user(
            username="nonemployer",
            email="nonemployer@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(non_employer)
        response = self.client.get(self.url)
        # In the view, if Employer.DoesNotExist is raised, a 403 response is returned.
        self.assertEqual(response.status_code, 403)
        
    def test_get_all_candidates(self):
        """Test that a GET request returns the correct candidates and context data."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn("candidates", context)
        self.assertIn("jobs", context)
        self.assertIn("statuses", context)
        self.assertIn("disciplines", context)
        
        # There should be 2 candidates.
        self.assertEqual(context["candidates"].count(), 2)
        # Check that the jobs passed in context are the employer's jobs.
        self.assertEqual(context["jobs"].count(), 2)
        # Disciplines should be a list of tuples. Check that it includes our disciplines.
        disciplines_list = [label for val, label in context["disciplines"]]
        self.assertIn("Bachelors", disciplines_list)
        self.assertIn("Masters", disciplines_list)

    def test_filter_by_job(self):
        """Test that filtering by a specific job returns only candidates for that job."""
        response = self.client.get(self.url, {"job": self.job1.id})
        self.assertEqual(response.status_code, 200)
        candidates = response.context["candidates"]
        # Only candidate1 applied to job1.
        self.assertEqual(candidates.count(), 1)
        self.assertEqual(candidates.first().job.id, self.job1.id)

    def test_filter_by_status(self):
        """Test that filtering by application status returns only matching candidates."""
        response = self.client.get(self.url, {"status": "Hired"})
        self.assertEqual(response.status_code, 200)
        candidates = response.context["candidates"]
        self.assertEqual(candidates.count(), 1)
        self.assertEqual(candidates.first().application_status, "Hired")

    def test_filter_by_discipline(self):
        """Test that filtering by discipline returns only candidates with that discipline."""
        response = self.client.get(self.url, {"discipline": "bachelors"})
        self.assertEqual(response.status_code, 200)
        candidates = response.context["candidates"]
        self.assertEqual(candidates.count(), 1)
        self.assertEqual(candidates.first().discipline, "bachelors")
