from django.test import TestCase
from tutorials.models.user_model import User
from tutorials.models.employer_models import Employer, Job, Candidate, Interview
from datetime import date, time

class InterviewModelTest(TestCase):

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
        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=date(2025, 6, 1),
            time=time(14, 30),
            interview_link="https://zoom.com/meeting123"
        )

    def test_create_interview(self):
        """Test interview instance creation."""
        interview = Interview.objects.get(candidate=self.candidate)
        self.assertEqual(interview.job.title, "Software Engineer")
        self.assertEqual(interview.interview_link, "https://zoom.com/meeting123")

    def test_interview_str_representation(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.interview), "Interview for john_doe - Software Engineer on 2025-06-01")
