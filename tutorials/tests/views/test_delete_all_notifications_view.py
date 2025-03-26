from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification
from django.http import JsonResponse

User = get_user_model()

class DeleteAllNotificationsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create an admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass',
            role='Admin',
            is_staff=True,
            is_superuser=True
        )

        # Create another user (non-admin)
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass',
            role='Employer'
        )

        # Create notifications for both users
        Notification.objects.create(
            recipient=self.admin_user,
            title='Admin Note 1',
            message='Hello',
            is_read=False,
            is_deleted=False
        )
        Notification.objects.create(
            recipient=self.other_user,
            title='Other Note',
            message='Hey',
            is_read=False,
            is_deleted=False
        )

        # Define the URL (adjust if named differently)
        self.url = reverse("admin_clear_all_notifications")


    def test_delete_all_notifications_success(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["count"], 2)

        # ✅ Confirm all admin’s notifications were deleted
        for n in Notification.objects.filter(recipient=self.admin_user):
            self.assertTrue(n.is_deleted)

        # ✅ Confirm other user's notifications were untouched
        for n in Notification.objects.filter(recipient=self.other_user):
            self.assertFalse(n.is_deleted)


    def test_delete_all_notifications_requires_post(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_redirects_if_not_admin(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)
        # Because of @user_passes_test, should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/log_in", response.url)

    def test_handles_exception_and_returns_500(self):
        self.client.force_login(self.admin_user)

        # Patch the queryset update to raise an exception
        original_filter = Notification.objects.filter

        def exploding_filter(*args, **kwargs):
            raise Exception("DB exploded")

        Notification.objects.filter = exploding_filter

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(response.content, {
            "success": False,
            "error": "DB exploded"
        })

        # Restore
        Notification.objects.filter = original_filter
