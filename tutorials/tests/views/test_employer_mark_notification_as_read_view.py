from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Employer, EmployerNotification

User = get_user_model()

class MarkNotificationAsReadViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an employer user.
        self.user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.user)
        # Create an Employer instance linked to the user.
        self.employer = Employer.objects.create(
            user=self.user,
            username="employeruser",  # Must match request.user.username
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        # Create an EmployerNotification for this employer.
        self.notification = EmployerNotification.objects.create(
            employer=self.employer,
            title="Test Notification",
            message="Notification message",
            is_read=False
        )
        # Build URL for the view.
        self.url = reverse("mark_notification_as_read", kwargs={"notification_id": self.notification.id})

    def test_mark_notification_as_read_success(self):
        """Test that a valid POST marks the notification as read."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        # Reload the notification from the database.
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_employer_not_found(self):
        """Test that if the logged-in user does not have an Employer instance, a JSON error with status 403 is returned."""
        # Delete the Employer instance.
        self.employer.delete()
        url = reverse("mark_notification_as_read", kwargs={"notification_id": self.notification.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error"), "Employer profile not found")

    def test_notification_not_found(self):
        """Test that if the notification does not exist for the employer, a JSON error with status 404 is returned."""
        # Use an invalid notification_id.
        invalid_url = reverse("mark_notification_as_read", kwargs={"notification_id": self.notification.id + 9999})
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertEqual(data.get("error"), "Notification not found")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
