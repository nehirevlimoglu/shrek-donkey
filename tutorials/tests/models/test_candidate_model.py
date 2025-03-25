from django.test import TestCase
from datetime import date
from tutorials.models.user_model import User
from tutorials.models.employer_models import Employer, Job, Candidate, WorkExperience

class CandidateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="john_doe", email="john@example.com", password="pass1234")

        self.employer = Employer.objects.create(
            user=self.user,
            username="tech_hub",
            email="contact@techhub.com",
            company_name="TechHub",
            company_location="San Francisco",
            industry="Tech"
        )

        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            company_name="TechHub",
            location="San Francisco",
            description="Test job"
        )

        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            application_status="Pending",
            first_name="John",
            last_name="Doe",
            phone="1234567890",
            address="123 Main St",
            school="Test University",
            degree="BSc Computer Science",
            discipline="Software Engineering",
            start_date=date(2020, 1, 1),
            end_date=date(2024, 1, 1),
            current_job_title="Junior Dev",
            current_employer="New Company",
            linkedin_profile="https://linkedin.com/in/johndoe",
            portfolio_website="https://johndoe.dev",
            how_did_you_hear="LinkedIn"
        )

        # ✅ Add related work experience separately
        WorkExperience.objects.create(
            candidate=self.candidate,
            job_title="Intern",
            employer="Old Company",
            start_date=date(2022, 6, 1),
            end_date=date(2023, 6, 1),
            job_description="Did lots of testing."
        )

    def test_create_candidate(self):
        candidate = Candidate.objects.get(user=self.user)
        self.assertEqual(candidate.job.title, "Software Engineer")
        self.assertEqual(candidate.application_status, "Pending")
        self.assertEqual(candidate.first_name, "John")

    def test_candidate_str_representation(self):
        self.assertEqual(str(self.candidate), "john_doe - Software Engineer")

    def test_default_skills_field(self):
        self.assertEqual(self.candidate.skills, "[]")

    def test_null_resume_and_cover_letter(self):
        self.assertFalse(self.candidate.resume)
        self.assertFalse(self.candidate.cover_letter)

    def test_optional_fields_can_be_blank(self):
        user2 = User.objects.create_user(username="jane_doe", email="jane@example.com", password="pass1234")
        candidate2 = Candidate.objects.create(user=user2)
        self.assertIsNone(candidate2.first_name)
        self.assertEqual(candidate2.application_status, "Pending")
