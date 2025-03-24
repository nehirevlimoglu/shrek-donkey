from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tutorials.models.admin_models import Notification  # Adjust import as needed

User = get_user_model()

class GenerateAdminNotificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user with the necessary flags so that is_admin passes.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        # Get the URL for generating a notification.
        self.url = reverse("admin_notifications_generate")

    def test_generate_notification_redirect(self):
        """Test that the view redirects to admin notifications page after generating a notification."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("admin_notifications"))

    def test_notification_created(self):
        """Test that a notification is created with the expected details."""
        initial_count = Notification.objects.count()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        # Ensure that one notification has been created.
        new_count = Notification.objects.count()
        self.assertEqual(new_count, initial_count + 1)
        # Get the latest notification and verify its fields.
        notif = Notification.objects.latest('id')
        self.assertEqual(notif.recipient, self.admin_user)
        self.assertEqual(notif.title, "Test Notification")
        self.assertEqual(notif.message, "This is a test notification for admin users.")
        self.assertEqual(notif.notification_type, "general")
        self.assertEqual(notif.priority, "medium")
        self.assertFalse(notif.is_read)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
