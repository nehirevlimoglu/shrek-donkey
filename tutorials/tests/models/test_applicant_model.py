# file: tutorials/tests/models/test_applicant_model.py

import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

# Adjust these imports to match your actual modules:
from tutorials.models.user_model import User
from tutorials.models.applicants_models import Applicant


class ApplicantModelTest(TestCase):
    def setUp(self):
        """
        Create a base User instance for reuse in tests.
        """
        self.user = User.objects.create(username="testuser", email="test@example.com")

    def test_create_applicant_minimal_fields(self):
        """
        Ensure we can create an Applicant with only the required field (user).
        Optional fields should remain blank/null without error.
        """
        applicant = Applicant.objects.create(user=self.user)

        self.assertEqual(applicant.user.username, "testuser")
        self.assertIsNone(applicant.degree)
        # For FileField with no file, the field is a FieldFile but 'falsy'.
        self.assertFalse(applicant.cv, "Expected no file attached.")
        self.assertEqual(applicant.salary_preferences, "")
        self.assertEqual(applicant.job_preferences, "")
        self.assertEqual(applicant.location_preferences, "")

    def test_blank_and_null_behavior(self):
        """
        Confirm that optional fields can be blank or null without causing errors.
        """
        applicant = Applicant.objects.create(
            user=self.user,
            degree=None,
            cv=None,
            salary_preferences="",
            job_preferences="",
            location_preferences=""
        )
        self.assertIsNone(applicant.degree)
        self.assertFalse(applicant.cv, "Expected no file attached.")
        self.assertEqual(applicant.salary_preferences, "")
        self.assertEqual(applicant.job_preferences, "")
        self.assertEqual(applicant.location_preferences, "")

    def test_create_applicant_with_all_fields(self):
        """
        Create an Applicant with all fields populated, including an uploaded file.
        """
        fake_cv = SimpleUploadedFile(
            "test_cv.pdf",
            b"Dummy content",
            content_type="application/pdf"
        )
        applicant = Applicant.objects.create(
            user=self.user,
            degree="MBA",
            cv=fake_cv,
            salary_preferences="60k-80k",
            job_preferences="Software, Data, Analytics",
            location_preferences="Remote, New York"
        )
        self.assertEqual(applicant.degree, "MBA")

        # Instead of checking for "test_cv.pdf" exactly, do a flexible check:
        self.assertIn("uploads/cv/", applicant.cv.name, "File not stored in the expected folder.")
        self.assertTrue(
            applicant.cv.name.startswith("uploads/cv/test_cv_"),
            f"Unexpected CV file name: {applicant.cv.name}"
        )

        self.assertEqual(applicant.salary_preferences, "60k-80k")
        self.assertEqual(applicant.job_preferences, "Software, Data, Analytics")
        self.assertEqual(applicant.location_preferences, "Remote, New York")

    def test_str_representation_with_degree(self):
        """
        __str__ should return "<username> - <degree>" if degree is set.
        """
        applicant_with_degree = Applicant.objects.create(
            user=self.user,
            degree="Computer Science"
        )
        self.assertEqual(str(applicant_with_degree), "testuser - Computer Science")

    def test_str_representation_no_degree(self):
        """
        If degree is None, __str__ should show "No Degree".
        """
        applicant_no_degree = Applicant.objects.create(user=self.user)
        self.assertEqual(str(applicant_no_degree), "testuser - No Degree")

    def test_degree_max_length_validation(self):
        """
        Exceeding the max_length on degree (255) should raise ValidationError
        when full_clean() is called.
        """
        long_degree = "x" * 300  # 300 chars, over the 255 limit
        applicant = Applicant(user=self.user, degree=long_degree)
        with self.assertRaises(ValidationError):
            applicant.full_clean()

    def test_one_to_one_constraint(self):
        """
        OneToOneField prevents creating another Applicant for the same User.
        """
        Applicant.objects.create(user=self.user, degree="First Degree")
        with self.assertRaises(IntegrityError):
            Applicant.objects.create(user=self.user, degree="Second Degree")

    def test_file_upload_path(self):
        """
        Check that the CV is saved under the defined path (uploads/cv/).
        """
        fake_cv = SimpleUploadedFile(
            "resume.pdf",
            b"Dummy file content",
            content_type="application/pdf"
        )
        applicant = Applicant.objects.create(user=self.user, cv=fake_cv)

        # Check it's in the correct folder
        self.assertIn("uploads/cv/", applicant.cv.name)

        # Instead of looking for "resume.pdf" exactly, check it starts with "resume_"
        self.assertTrue(
            applicant.cv.name.startswith("uploads/cv/resume_"),
            f"Unexpected file name: {applicant.cv.name}"
        )

   