from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from tutorials.models.admin_models import Admin, Notification
from tutorials.models.employer_models import Employer

User = get_user_model()

class MarkNotificationAsReadViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user using the User model.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        # Create an Admin instance linked to the admin user.
        self.admin_instance = Admin.objects.create(
            user=self.admin_user,
            username="adminuser",
            email="admin@example.com"
        )
        # Explicitly attach the admin instance to the user so that user.admin exists.
        setattr(self.admin_user, 'admin', self.admin_instance)
        self.admin_user.refresh_from_db()  # Ensure updated

        # Create a sample notification (unread, not deleted) for this admin.
        self.notification = Notification.objects.create(
            title="Test Notification",
            message="This is a test notification.",
            notification_type="general",
            priority="medium",
            is_read=False,
            is_deleted=False,
            created_at=timezone.now(),
            recipient=self.admin_user  # Make sure the recipient is set to admin_user
        )
        # Use the correct URL name (e.g. "admin_mark_notification_as_read") here.
        self.url = reverse("admin_mark_notification_as_read", kwargs={"notification_id": self.notification.id})
        self.client.force_login(self.admin_user)

    def test_mark_notification_as_read_successful(self):
        """Test that a valid POST request marks the notification as read and returns JSON success."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data.get("status"), "success")
        # Reload the notification from the DB.
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_invalid_method_get(self):
        """Test that a GET request is not allowed (405 Method Not Allowed)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected."""
        self.client.logout()
        response = self.client.post(self.url)
        login_url = reverse("log_in")  # Adjust if your login URL is named differently.
        expected_redirect = f"{login_url}?next={self.url}"
        self.assertRedirects(response, expected_redirect)
