from django.test import TestCase
from tutorials.forms.employer_forms import JobForm, get_job_titles, EmployerProfileForm
from tutorials.models.employer_models import Job
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
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

    def test_get_job_titles_file_exists(self):
        """Test get_job_titles() reads titles correctly from file."""
        json_path = os.path.join(settings.BASE_DIR, 'static/data/job_titles.json')
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        sample_titles = ["Engineer", "Designer"]
        with open(json_path, 'w') as file:
            json.dump(sample_titles, file)

        result = get_job_titles()
        expected = [("Engineer", "Engineer"), ("Designer", "Designer")]
        self.assertEqual(result, expected)

        os.remove(json_path)

    def test_form_initializes_with_user_data(self):
        """Test EmployerProfileForm pre-fills fields when user is provided."""
        User = get_user_model()
        user = User.objects.create_user(username='testuser', email='user@example.com', first_name='Test', last_name='User')

        form = EmployerProfileForm(user=user)
        self.assertEqual(form.fields['first_name'].initial, 'Test')
        self.assertEqual(form.fields['last_name'].initial, 'User')
        self.assertEqual(form.fields['email'].initial, 'user@example.com')


    def test_form_saves_user_info(self):
        """Test EmployerProfileForm.save updates user info when user is present."""
        User = get_user_model()
        user = User.objects.create_user(username='testuser2', email='old@example.com', first_name='Old', last_name='Name')

        # Create an Employer instance linked to the user (required due to NOT NULL constraint)
        from tutorials.models.employer_models import Employer
        employer_instance = Employer(user=user)  # Only setting user, form will populate the rest

        form_data = {
            "first_name": "New",
            "last_name": "Name",
            "email": "new@example.com",
            "company_name": "NewCo",
            "company_website": "https://newco.com",
            "industry": "Tech",
            "company_location": "Remote"
        }

        # Bind the form to that instance
        form = EmployerProfileForm(data=form_data, user=user, instance=employer_instance)
        self.assertTrue(form.is_valid())

        employer = form.save()

        user.refresh_from_db()
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(employer.company_name, "NewCo")


       