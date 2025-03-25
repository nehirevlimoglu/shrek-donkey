
# file: tutorials/tests/models/test_applicant_model.py

import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

# Adjust these imports to match your actual modules:
from tutorials.models.user_model import User
from tutorials.models.applicants_models import Applicant, JobTitle


class ApplicantModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", email="test@example.com")
        self.job_title = JobTitle.objects.create(title="Software Engineering")

    def test_create_applicant_minimal_fields(self):
        applicant = Applicant.objects.create(user=self.user)
        self.assertEqual(applicant.user.username, "testuser")
        self.assertIsNone(applicant.degree)
        self.assertFalse(applicant.cv, "Expected no file attached.")
        self.assertEqual(applicant.salary_preferences, "")
        self.assertEqual(applicant.location_preferences, "")
        self.assertEqual(applicant.job_preferences.count(), 0)

    def test_blank_and_null_behavior(self):
        applicant = Applicant.objects.create(
            user=self.user,
            degree=None,
            cv=None,
            salary_preferences="",
            location_preferences=""
        )
        applicant.job_preferences.set([])

        self.assertIsNone(applicant.degree)
        self.assertFalse(applicant.cv, "Expected no file attached.")
        self.assertEqual(applicant.salary_preferences, "")
        self.assertEqual(applicant.location_preferences, "")
        self.assertEqual(applicant.job_preferences.count(), 0)

    def test_create_applicant_with_all_fields(self):
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
            location_preferences="Remote, New York"
        )
        applicant.job_preferences.set([self.job_title])

        self.assertEqual(applicant.degree, "MBA")
        self.assertIn("uploads/cv/", applicant.cv.name, "File not stored in the expected folder.")
        self.assertTrue(
            applicant.cv.name.startswith("uploads/cv/test_cv_"),
            f"Unexpected CV file name: {applicant.cv.name}"
        )
        self.assertEqual(applicant.salary_preferences, "60k-80k")
        self.assertEqual(applicant.location_preferences, "Remote, New York")
        self.assertEqual(applicant.job_preferences.count(), 1)

    def test_str_representation_with_degree(self):
        applicant_with_degree = Applicant.objects.create(
            user=self.user,
            degree="Computer Science"
        )
        self.assertEqual(str(applicant_with_degree), "testuser - Computer Science")

    def test_str_representation_no_degree(self):
        applicant_no_degree = Applicant.objects.create(user=self.user)
        self.assertEqual(str(applicant_no_degree), "testuser - No Degree")

    def test_degree_max_length_validation(self):
        long_degree = "x" * 300
        applicant = Applicant(user=self.user, degree=long_degree)
        with self.assertRaises(ValidationError):
            applicant.full_clean()

    def test_one_to_one_constraint(self):
        Applicant.objects.create(user=self.user, degree="First Degree")
        with self.assertRaises(IntegrityError):
            Applicant.objects.create(user=self.user, degree="Second Degree")

    def test_file_upload_path(self):
        fake_cv = SimpleUploadedFile(
            "resume.pdf",
            b"Dummy file content",
            content_type="application/pdf"
        )
        applicant = Applicant.objects.create(user=self.user, cv=fake_cv)
        self.assertIn("uploads/cv/", applicant.cv.name)
        self.assertTrue(
            applicant.cv.name.startswith("uploads/cv/resume_"),
            f"Unexpected file name: {applicant.cv.name}"
        )
