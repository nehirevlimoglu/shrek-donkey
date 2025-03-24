from django.test import TestCase, Client
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification  # Adjust the import if needed
from tutorials.models.admin_models import Admin
from tutorials.models.employer_models import Employer

User = get_user_model()

class AdminNotificationsCountViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.admin_instance = Admin.objects.create(
            id=self.admin_user.id,
            username="adminuser_admin",
            email="admin_admin@example.com"
        )
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
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
        # Create several notifications.
        # We'll create 3 unread notifications and 2 read notifications.
        Notification.objects.create(
            title="Notif 1",
            message="Message 1",
            notification_type="general",
            priority="high",
            is_read=False,
            is_deleted=False
        )
        Notification.objects.create(
            title="Notif 2",
            message="Message 2",
            notification_type="job",
            priority="medium",
            is_read=False,
            is_deleted=False
        )
        Notification.objects.create(
            title="Notif 3",
            message="Message 3",
            notification_type="application",
            priority="low",
            is_read=False,
            is_deleted=False
        )
        # Read notifications should not be counted.
        Notification.objects.create(
            title="Notif 4",
            message="Message 4",
            notification_type="user",
            priority="low",
            is_read=True,
            is_deleted=False
        )
        # Deleted notifications should not be counted.
        Notification.objects.create(
            title="Notif 5",
            message="Message 5",
            notification_type="system",
            priority="medium",
            is_read=False,
            is_deleted=True
        )

        # Expected unread count is 3.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # The view returns JSON with key 'count'
        json_data = response.json()
        self.assertIn("count", json_data)
        self.assertEqual(json_data["count"], 3)
