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
        # Create a temporary directory with the expected folder structure,
        # but without creating the JSON file.
        with tempfile.TemporaryDirectory() as tmpdirname:
            static_data_dir = os.path.join(tmpdirname, "static", "data")
            os.makedirs(static_data_dir, exist_ok=True)
            json_path = os.path.join(static_data_dir, "job_titles.json")
            # Ensure file does not exist.
            if os.path.exists(json_path):
                os.remove(json_path)

            with override_settings(BASE_DIR=tmpdirname):
                populate_job_titles(DummySender())
                # No job titles should have been added.
                self.assertEqual(JobTitle.objects.count(), 0)

    def test_populate_job_titles_file_found(self):
        """
        Test that when the job_titles.json file exists, the signal
        reads the file and creates JobTitle objects.
        """
        sample_titles = ["Data Scientist", "Project Manager", "Designer"]
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Create the static/data directory.
            static_data_dir = os.path.join(tmpdirname, "static", "data")
            os.makedirs(static_data_dir, exist_ok=True)
            json_path = os.path.join(static_data_dir, "job_titles.json")
            # Write sample job titles to the file.
            with open(json_path, 'w') as f:
                json.dump(sample_titles, f)

            with override_settings(BASE_DIR=tmpdirname):
                populate_job_titles(DummySender())
                # Verify that the number of JobTitle objects equals the number of titles in the file.
                self.assertEqual(JobTitle.objects.count(), len(sample_titles))
                for title in sample_titles:
                    self.assertTrue(JobTitle.objects.filter(title=title).exists())
