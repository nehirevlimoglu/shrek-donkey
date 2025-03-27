from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification  # Adjust the import if needed
from tutorials.models.employer_models import Employer

User = get_user_model()

class AdminNotificationsCountViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create the admin using the proper user model
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin"
        )

        # Optionally, if your app uses Employer for admin notifications, create an employer
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="adminuser",
            email="admin@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )

        self.url = reverse("admin_notifications_count")
        self.client.force_login(self.admin_user)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users cannot access the notifications count view."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_notifications_count(self):
        """Test that the view returns the correct count of unread, not-deleted notifications."""
        # Create 3 unread notifications and 2 that shouldn't be counted.
        Notification.objects.create(
            title="Notif 1",
            message="Message 1",
            recipient=self.admin_user,
            notification_type="general",
            priority="high",
            is_read=False,
            is_deleted=False
        )
        Notification.objects.create(
            title="Notif 2",
            message="Message 2",
            recipient=self.admin_user,
            notification_type="job",
            priority="medium",
            is_read=False,
            is_deleted=False
        )
        Notification.objects.create(
            title="Notif 3",
            message="Message 3",
            recipient=self.admin_user,
            notification_type="application",
            priority="low",
            is_read=False,
            is_deleted=False
        )
        # Read notification (should not count)
        Notification.objects.create(
            title="Notif 4",
            message="Message 4",
            recipient=self.admin_user,
            notification_type="user",
            priority="low",
            is_read=True,
            is_deleted=False
        )
        # Deleted notification (should not count)
        Notification.objects.create(
            title="Notif 5",
            message="Message 5",
            recipient=self.admin_user,
            notification_type="system",
            priority="medium",
            is_read=False,
            is_deleted=True
        )

        # Expected unread count is 3.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("count", json_data)
        self.assertEqual(json_data["count"], 3)
