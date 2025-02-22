from django.test import TestCase
from tutorials.forms.employer_forms import JobForm, get_job_titles
from tutorials.models.employer_models import Job
from django.core.exceptions import ValidationError
from django.conf import settings
import os
import json

class JobFormTest(TestCase):

    def setUp(self):
        """Set up valid job data for testing."""
        self.valid_data = {
            "title": "Software Engineer",
            "position": "Software Engineer",
            "company_name": "TechCorp",
            "location": "New York",
            "job_type": "Full Time",
            "salary": "100000",
            "description": "Develop software solutions.",
            "requirements": "Experience in Python.",
            "benefits": "Health insurance, 401k.",
            "application_deadline": "2025-12-31",
            "contact_email": "hr@techcorp.com"
        }

    def test_valid_job_form(self):
        """Test form validation with valid data."""
        form = JobForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        """Test form validation fails when required fields are missing."""
        invalid_data = self.valid_data.copy()
        del invalid_data["title"]  # Remove required field

        form = JobForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)  # Title field should raise an error

    def test_invalid_email(self):
        """Test invalid email format fails validation."""
        invalid_data = self.valid_data.copy()
        invalid_data["contact_email"] = "invalid-email"

        form = JobForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("contact_email", form.errors)  # Email should be invalid

    def test_non_numeric_salary(self):
        """Test non-numeric salary fails validation."""
        invalid_data = self.valid_data.copy()
        invalid_data["salary"] = "invalid_salary"  # Non-numeric input

        form = JobForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("salary", form.errors)  # Salary should be numeric

    def test_get_job_titles_file_not_found(self):
        """Test get_job_titles() returns 'Other' when file is missing."""
        json_path = os.path.join(settings.BASE_DIR, 'static/data/job_titles.json')

        # Rename the file temporarily if it exists
        temp_path = json_path + ".backup"
        if os.path.exists(json_path):
            os.rename(json_path, temp_path)

        try:
            self.assertEqual(get_job_titles(), [("Other", "Other")])
        finally:
            # Restore the file if it was renamed
            if os.path.exists(temp_path):
                os.rename(temp_path, json_path)
