from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification

User = get_user_model()

class GenerateAdminNotificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpass",
            role="Admin",
            is_staff=True,
        )

        self.non_admin_user = User.objects.create_user(
            username="normaluser",
            email="user@example.com",
            password="userpass",
            role="Applicant",
            is_staff=False,
        )

        # ✅ Corrected URL name here:
        self.url = reverse("admin_notifications_generate")

    def test_admin_can_generate_notification(self):
        self.client.login(username="adminuser", password="adminpass")

        # Count before
        before_count = Notification.objects.count()

        response = self.client.get(self.url)

        # Should redirect to admin_notifications
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("admin_notifications"))

        # Notification count should increase
        self.assertEqual(Notification.objects.count(), before_count + 1)

        # Fetch the new one
        notification = Notification.objects.latest("id")
        self.assertEqual(notification.recipient, self.admin_user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertFalse(notification.is_read)


    def test_non_admin_cannot_generate_notification(self):
        self.client.login(username="normaluser", password="userpass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Updated: Redirect to login by default

        # Optional: confirm where it's redirecting to
        login_url = reverse("log_in")
        self.assertTrue(response.url.startswith(login_url))

        # Notification should not be created
        self.assertEqual(Notification.objects.filter(recipient=self.non_admin_user).count(), 0)


    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
