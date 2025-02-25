from django.test import TestCase
from tutorials.models.user_model import User
from tutorials.models.employer_models import Employer, Job, Candidate

class CandidateModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="john_doe", email="john@example.com")
        self.employer = Employer.objects.create(username="tech_hub", email="contact@techhub.com", company_name="TechHub")
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            company_name="TechHub",
            location="San Francisco"
        )
        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            application_status="Pending"
        )

    def test_create_candidate(self):
        """Test candidate instance creation."""
        candidate = Candidate.objects.get(user=self.user)
        self.assertEqual(candidate.job.title, "Software Engineer")
        self.assertEqual(candidate.application_status, "Pending")

    def test_candidate_str_representation(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.candidate), "john_doe - Software Engineer")
