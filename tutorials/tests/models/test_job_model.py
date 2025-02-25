from django.test import TestCase
from tutorials.models.employer_models import Employer, Job

class JobModelTest(TestCase):

    def setUp(self):
        self.employer = Employer.objects.create(username="tech_hub", email="contact@techhub.com", company_name="TechHub")
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
            contact_email="hr@techhub.com"
        )

    def test_create_job(self):
        """Test job instance creation."""
        job = Job.objects.get(title="Software Engineer")
        self.assertEqual(job.company_name, "TechHub")
        self.assertEqual(job.job_type, "Full Time")

    def test_job_str_representation(self):
        """Test the __str__ method."""
        self.assertEqual(str(self.job), "Software Engineer")
