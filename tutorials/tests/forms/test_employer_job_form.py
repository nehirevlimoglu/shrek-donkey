from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.core.files.uploadedfile import SimpleUploadedFile
from tutorials.models.employer_models import Job, Employer
from tutorials.forms.employer_forms import JobForm, CustomPasswordChangeForm, EmployerProfileForm


class JobFormTest(TestCase):
    def test_valid_job_form(self):
        """Ensure JobForm validates correctly with valid data."""
        form_data = {
            "title": "Software Engineer",
            "position": "Engineer",
            "company_name": "TechCorp",
            "location": "New York",
            "job_type": "Full-time",
            "salary": "100000",
            "description": "Develop software solutions.",
            "requirements": "Experience in Python.",
            "benefits": "Health insurance, 401k.",
            "application_deadline": "2025-12-31",
            "contact_email": "hr@techcorp.com"
        }
        form = JobForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_fields(self):
        """Ensure JobForm fails validation if required fields are missing."""
        form_data = {
            "title": "",
            "description": "Some job description.",
            "requirements": "Some requirements."
        }
        form = JobForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("company_name", form.errors)  # Should fail as it's missing