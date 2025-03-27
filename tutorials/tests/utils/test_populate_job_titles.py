import os
import json
import tempfile
from django.test import TestCase, override_settings
from tutorials.models.employer_models import JobTitle, WorkExperience
from tutorials.signals import populate_job_titles  # Adjust the import path if needed

# Dummy sender to simulate the 'tutorials' app.
class DummySender:
    name = "tutorials"

class PopulateJobTitlesSignalTests(TestCase):
    def tearDown(self):
        # Clean up any JobTitle objects created during tests.
        JobTitle.objects.all().delete()

    def test_populate_job_titles_file_not_found(self):
        """
        Test that when the job_titles.json file does not exist,
        the signal prints a warning and does not create any JobTitle.
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            static_data_dir = os.path.join(tmpdirname, "static", "data")
            os.makedirs(static_data_dir, exist_ok=True)
            json_path = os.path.join(static_data_dir, "job_titles.json")
            if os.path.exists(json_path):
                os.remove(json_path)

            with override_settings(BASE_DIR=tmpdirname):
                populate_job_titles(DummySender())
                self.assertEqual(JobTitle.objects.count(), 0)

    def test_populate_job_titles_file_found(self):
        """
        Test that when the job_titles.json file exists, the signal
        reads the file and creates JobTitle objects.
        """
        sample_titles = ["Data Scientist", "Project Manager", "Designer"]
        # Clear any existing JobTitle objects before running the signal.
        JobTitle.objects.all().delete()

        with tempfile.TemporaryDirectory() as tmpdirname:
            static_data_dir = os.path.join(tmpdirname, "static", "data")
            os.makedirs(static_data_dir, exist_ok=True)
            json_path = os.path.join(static_data_dir, "job_titles.json")
            with open(json_path, 'w') as f:
                json.dump(sample_titles, f)

            with override_settings(BASE_DIR=tmpdirname):
                populate_job_titles(DummySender())
                # Instead of asserting exact count, ensure that each title exists.
                for title in sample_titles:
                    self.assertTrue(JobTitle.objects.filter(title=title).exists())
                # Alternatively, if you really want to check count:
                self.assertEqual(JobTitle.objects.count(), len(sample_titles))
