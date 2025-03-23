from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from tutorials.models.employer_models import Employer, Job

User = get_user_model()

class JobModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tech_hub_user",
            email="contact@techhub.com",
            password="testpassword123"
        )

        self.employer = Employer.objects.create(
            user=self.user,  # associating the User here
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
            job_type="Full Time",
            salary=120000,
            description="Develop software solutions.",
            requirements="Experience in Python.",
            benefits="Health insurance, 401k.",
            contact_email="hr@techhub.com",
            application_deadline=now().date() + timedelta(days=30),
            status="pending"
        )

    def test_create_job(self):
        """Test job instance creation."""
        job = Job.objects.get(title="Software Engineer")
        self.assertEqual(job.company_name, "TechHub")
        self.assertEqual(job.job_type, "Full Time")
        self.assertEqual(job.status, "pending")

    def test_job_str_representation(self):
        """Test the __str__ method."""
        expected_str = "Software Engineer (Pending Review)"
        self.assertEqual(str(self.job), expected_str)

    def test_extracted_skills_methods(self):
        """Test extracted skills getter and setter methods."""
        skills = ["Python", "Django", "REST"]
        self.job.set_extracted_skills(skills)
        self.job.save()

        retrieved_job = Job.objects.get(pk=self.job.pk)
        self.assertListEqual(retrieved_job.get_extracted_skills(), skills)

    def test_default_values(self):
        """Test default values of fields."""
        new_job = Job.objects.create(
            employer=self.employer,
            title="Data Analyst",
            description="Analyze data sets.",
        )
        self.assertEqual(new_job.company_name, "Unknown Company")
        self.assertEqual(new_job.location, "Unknown Location")
        self.assertEqual(new_job.contact_email, "default@email.com")
        self.assertEqual(new_job.status, "pending")
