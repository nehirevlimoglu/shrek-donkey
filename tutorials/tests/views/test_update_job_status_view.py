import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job, Employer
from tutorials.models.admin_models import Notification  # Use Notification, not EmployerNotification

User = get_user_model()

class UpdateJobStatusViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        # Create an admin user with necessary flags.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        
        # Create an Employer instance for the job.
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )
        
        # Create a Job instance for testing.
        # Start with a job that has a future deadline and status 'pending'.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job for status update testing",
            application_deadline=self.today + timedelta(days=10),
            status="pending"
        )
        self.url = reverse("update_job_status")
    
    def post_update(self, job_id, new_status):
        payload = {"job_id": job_id, "status": new_status}
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
    
    def test_method_not_allowed(self):
        """Test that GET requests return 405 Method Not Allowed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
    
    def test_missing_job_id_or_status(self):
        """Test that missing job_id or status returns 400."""
        # Missing job_id:
        payload = {"status": "Open"}
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        
        # Missing status:
        payload = {"job_id": self.job.id}
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
    
    def test_job_not_found(self):
        """Test that an invalid job_id returns 404."""
        payload = {"job_id": 99999, "status": "Open"}
        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data.get("error"), "Job not found")
    
    def test_toggle_status_open(self):
        """
        Test that new_status 'Open' sets the deadline to 30 days in the future.
        Also, if current status is 'rejected', it should be reset to 'pending'.
        """
        # Set initial job status to pending.
        self.job.status = "pending"
        self.job.save()
        response = self.post_update(self.job.id, "Open")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.job.refresh_from_db()
        expected_deadline = timezone.now().date() + timedelta(days=30)
        self.assertEqual(self.job.application_deadline, expected_deadline)
        # If status was pending, it remains unchanged.
        self.assertEqual(self.job.status, "pending")
        
        # Now set status to 'rejected' and test that it becomes 'pending'
        self.job.status = "rejected"
        self.job.save()
        response = self.post_update(self.job.id, "Open")
        self.assertEqual(response.status_code, 200)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "pending")

    def test_toggle_status_closed(self):
        """Test that new_status 'Closed' sets the deadline to 2 days ago and leaves status unchanged."""
        response = self.post_update(self.job.id, "Closed")
        self.assertEqual(response.status_code, 200)
        self.job.refresh_from_db()
        expected_deadline = timezone.now().date() - timedelta(days=2)
        self.assertEqual(self.job.application_deadline, expected_deadline)
        # The status field should not be changed by 'Closed' branch.
        self.assertEqual(self.job.status, "pending")

    def test_toggle_status_approved(self):
        """
        Test that new_status 'approved' sets job status to 'approved' and deadline is set to 30 days in the future if needed.
        Also, a notification is sent.
        """
        # Set the deadline to past to force update.
        self.job.application_deadline = timezone.now().date() - timedelta(days=5)
        self.job.save()
        initial_notifications = Notification.objects.count()
        
        response = self.post_update(self.job.id, "approved")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "approved")
        expected_deadline = timezone.now().date() + timedelta(days=30)
        self.assertEqual(self.job.application_deadline, expected_deadline)
        
        # Check that an approval notification was sent.
        final_notifications = Notification.objects.count()
        self.assertEqual(final_notifications, initial_notifications + 1)

    def test_toggle_status_rejected(self):
        """Test that new_status 'rejected' sets job status to 'rejected' and deadline to 2 days ago."""
        response = self.post_update(self.job.id, "rejected")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "rejected")
        expected_deadline = timezone.now().date() - timedelta(days=2)
        self.assertEqual(self.job.application_deadline, expected_deadline)

    def test_unrecognized_status(self):
        """Test that an unrecognized status doesn't break the view (and returns success)."""
        original_deadline = self.job.application_deadline
        original_status = self.job.status
        response = self.post_update(self.job.id, "UnknownStatus")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.job.refresh_from_db()
        # With an unrecognized status, the view logs a warning but does not change the deadline/status.
        self.assertEqual(self.job.application_deadline, original_deadline)
        self.assertEqual(self.job.status, original_status)
