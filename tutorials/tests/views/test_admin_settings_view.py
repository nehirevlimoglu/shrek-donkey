import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model, update_session_auth_hash

from tutorials.models.employer_models import Employer
from tutorials.models.admin_models import Admin, NotificationPreference

User = get_user_model()

class AdminSettingsViewTests(TestCase):

    def setUp(self):
        """Set up test data for the admin_settings view."""
        self.client = Client()
        # Create an admin user with the appropriate flags so that is_admin passes.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        # Force login as the admin user.
        self.client.force_login(self.admin_user)
        # Create an Admin instance with the same id as the admin user.
        self.admin_instance = Admin.objects.create(
            id=self.admin_user.id,
            username=self.admin_user.username,
            email=self.admin_user.email
            # Add additional required fields if your model needs them.
        )
        # Create an Employer instance (if your view depends on it).
        self.employer = Employer.objects.create(
            user=self.admin_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )
        self.url = reverse("admin_settings")

    def test_get_admin_settings_default(self):
        """Test GET request returns default admin settings context with default notification preferences."""
        # Ensure no NotificationPreference exists.
        NotificationPreference.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        context = response.context
        self.assertIn("tab", context)
        self.assertIn("admin", context)
        self.assertIn("user", context)
        self.assertIn("error", context)
        self.assertIn("notification_prefs", context)
        # When no preferences exist, defaults should be provided.
        np = context["notification_prefs"]
        self.assertTrue(np["job_notifications"])
        self.assertTrue(np["application_notifications"])
        self.assertTrue(np["user_notifications"])
        self.assertTrue(np["system_notifications"])
        self.assertTrue(np["email_delivery"])
        self.assertTrue(np["dashboard_delivery"])

    def test_update_profile_successful(self):
        """Test that posting a valid profile update changes user and admin fields."""
        data = {
            "update_profile": "1",
            "username": "newadminuser",
            "email": "newadmin@example.com",
            "first_name": "New",
            "last_name": "Admin",
            "phone_number": "1234567890",
        }
        response = self.client.post(self.url, data)
        # Expect a redirect on successful update.
        self.assertEqual(response.status_code, 302)
        # Verify the User has been updated.
        user = User.objects.get(pk=self.admin_user.id)
        self.assertEqual(user.username, "newadminuser")
        self.assertEqual(user.email, "newadmin@example.com")
        # Verify the Admin-specific field.
        admin = Admin.objects.get(pk=self.admin_user.id)
        self.assertEqual(admin.phone_number, "1234567890")

    def test_update_profile_username_exists(self):
        """Test that profile update fails if the new username already exists."""
        # Create another user with a conflicting username.
        existing_user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="password123",
            role="Applicant"
        )
        data = {
            "update_profile": "1",
            "username": "existinguser",  # conflict username
            "email": "newadmin@example.com",
            "first_name": "New",
            "last_name": "Admin",
            "phone_number": "1234567890",
        }
        response = self.client.post(self.url, data)
        # Expect the view to re-render the form with an error (status 200).
        self.assertEqual(response.status_code, 200)
        self.assertIn("Username already exists", response.content.decode())

    def test_change_password_incorrect_current(self):
        """Test that an incorrect current password returns an error and re-renders the form."""
        data = {
            "change_password": "1",
            "current_password": "wrongpassword",
            "new_password": "newstrongpassword",
            "confirm_password": "newstrongpassword"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Current password is incorrect", response.content.decode())

    def test_change_password_mismatch(self):
        """Test that mismatched new passwords return an error."""
        data = {
            "change_password": "1",
            "current_password": "password123",
            "new_password": "newstrongpassword",
            "confirm_password": "differentpassword"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("New passwords do not match", response.content.decode())

    def test_change_password_too_short(self):
        """Test that a new password shorter than 8 characters returns an error."""
        data = {
            "change_password": "1",
            "current_password": "password123",
            "new_password": "short",
            "confirm_password": "short"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Password must be at least 8 characters long", response.content.decode())

    def test_change_password_successful(self):
        """Test that a valid password change updates the password and keeps the user logged in."""
        data = {
            "change_password": "1",
            "current_password": "password123",
            "new_password": "newstrongpassword",
            "confirm_password": "newstrongpassword"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        # Logout and attempt login with new password.
        self.client.logout()
        login_success = self.client.login(username="adminuser", password="newstrongpassword")
        self.assertTrue(login_success)

    def test_update_notification_preferences_successful(self):
        """Test that posting notification preferences creates/updates them correctly."""
        data = {
            "update_notification_prefs": "1",
            "job_notifications": "on",
            "application_notifications": "on",
            "user_notifications": "on",
            "system_notifications": "on",
            "email_delivery": "on",
            "dashboard_delivery": "on",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        # Verify that NotificationPreference is created and updated.
        np = NotificationPreference.objects.get(admin__id=self.admin_user.id)
        self.assertTrue(np.job_notifications)
        self.assertTrue(np.application_notifications)
        self.assertTrue(np.user_notifications)
        self.assertTrue(np.system_notifications)
        self.assertTrue(np.email_delivery)
        self.assertTrue(np.dashboard_delivery)

    def test_notification_preferences_default_on_get(self):
        """Test that when no NotificationPreference exists, default values are provided."""
        # Remove any existing preferences.
        NotificationPreference.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        np = response.context["notification_prefs"]
        self.assertTrue(np["job_notifications"])
        self.assertTrue(np["application_notifications"])
        self.assertTrue(np["user_notifications"])
        self.assertTrue(np["system_notifications"])
        self.assertTrue(np["email_delivery"])
        self.assertTrue(np["dashboard_delivery"])

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_non_admin_user_redirected(self):
        """Test that a logged-in user without admin privileges is redirected."""
        non_admin = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(non_admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
