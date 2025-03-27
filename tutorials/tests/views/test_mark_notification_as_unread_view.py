import json
from django.test import TestCase, Client, override_settings
from django.urls import path, reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch

from tutorials.views.admin_views import mark_notification_as_unread  # Adjust the import path if needed
from tutorials.models.admin_models import Notification
from tutorials.models.employer_models import Employer, Job, Candidate
from django.contrib.auth.views import LoginView


User = get_user_model()

# Define temporary URL patterns for testing.
urlpatterns = [
    path(
        'admin_notifications/mark_unread/<int:notification_id>/',
        mark_notification_as_unread,
        name='admin_mark_notification_as_unread'
    ),
]


@override_settings(ROOT_URLCONF=__name__)
class MarkNotificationAsUnreadViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        # Create an Employer instance linked to the admin user.
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="adminuser",
            email="admin@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        # Create a dummy job.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Dummy Job",
            description="A dummy job",
            application_deadline=timezone.now().date() + timezone.timedelta(days=10),
            contact_email="dummy@example.com"
        )
        # Create a Candidate with an associated job.
        self.candidate = Candidate.objects.create(
            user=self.admin_user,
            job=self.job,
            first_name="Admin",
            last_name="User"
        )
        # Create a sample notification for this admin.
        self.notification = Notification.objects.create(
            title="Test Notification",
            message="This is a test notification.",
            notification_type="general",
            priority="medium",
            is_read=True,  # start as read so we can mark it unread
            is_deleted=False,
            created_at=timezone.now(),
            recipient=self.admin_user
        )
        # Use the correct URL name.
        self.url = reverse("admin_mark_notification_as_unread", kwargs={"notification_id": self.notification.id})
        self.client.force_login(self.admin_user)

    def test_mark_notification_as_unread_successful(self):
        """Test that a valid POST request marks the notification as unread and returns JSON success."""
        # Ensure the notification is marked read initially.
        self.notification.is_read = True
        self.notification.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        # Reload the notification from the DB.
        self.notification.refresh_from_db()
        self.assertFalse(self.notification.is_read)

    def test_notification_not_found(self):
        """Test that a POST for a non-existent notification returns 404."""
        url = reverse("admin_mark_notification_as_unread", kwargs={"notification_id": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("message"), "Notification not found")

    def test_permission_denied(self):
        """Test that if the notification does not belong to the logged-in user, a 403 is returned."""
        other_admin = User.objects.create_user(
            username="otheradmin",
            email="otheradmin@example.com",
            password="otherpass",
            role="Admin"
        )
        other_notification = Notification.objects.create(
            title="Oops",
            message="Private",
            notification_type="general",
            priority="medium",
            is_read=True,
            is_deleted=False,
            created_at=timezone.now(),
            recipient=other_admin
        )
        url = reverse("admin_mark_notification_as_unread", kwargs={"notification_id": other_notification.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data.get("status"), "error")
        self.assertEqual(data.get("message"), "Permission denied")

    def test_method_not_allowed(self):
        """Test that a GET request is not allowed (405 Method Not Allowed)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

