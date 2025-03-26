from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification

User = get_user_model()

class MarkNotificationAsReadViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            role='Admin',
            is_staff=True,
            is_superuser=True
        )

        # Non-admin user
        self.other_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass',
            role='Employer'
        )

        # Notification for admin
        self.notification = Notification.objects.create(
            recipient=self.admin_user,
            title='Test',
            message='Hello',
            is_read=False,
            is_deleted=False
        )

        self.url = reverse("admin_mark_notification_as_read", kwargs={"notification_id": self.notification.id})

    def test_admin_can_mark_own_notification_as_read(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success"})
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_get_method_not_allowed(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_non_admin_user_gets_403(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {
            "status": "error",
            "message": "User is not an admin"
        })


    def test_admin_cannot_mark_other_users_notification(self):
        other_notification = Notification.objects.create(
            recipient=self.other_user,
            title='Oops',
            message='Private',
            is_read=False
        )
        self.client.force_login(self.admin_user)
        url = reverse("admin_mark_notification_as_read", kwargs={"notification_id": other_notification.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {
            "status": "error",
            "message": "Permission denied"
        })

    def test_notification_does_not_exist(self):
        self.client.force_login(self.admin_user)
        url = reverse("admin_mark_notification_as_read", kwargs={"notification_id": 9999})  # Nonexistent
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(response.content, {
            "status": "error",
            "message": "Notification not found"
        })

    def test_server_exception_returns_500(self):
        self.client.force_login(self.admin_user)

        # Monkey-patch Notification.objects.get to raise an exception
        original_get = Notification.objects.get
        Notification.objects.get = lambda *args, **kwargs: 1 / 0  # division by zero

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["status"], "error")

        # Restore original
        Notification.objects.get = original_get
