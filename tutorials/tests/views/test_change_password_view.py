from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.messages import get_messages

User = get_user_model()

class ChangePasswordViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test user (employer) with a known password.
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="oldpassword123",
            role="Employer"
        )
        # Force-login the user.
        self.client.force_login(self.user)
        # URL for change_password view (assumed to be named "change_password")
        self.url = reverse("change_password")

    def test_get_change_password_view(self):
        """Test that a GET request returns the change password form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "change_password.html")
        # Ensure the form is in context.
        self.assertIn("form", response.context)

    def test_post_valid_change_password(self):
        """Test that a valid POST request changes the password and redirects to employer_settings."""
        valid_data = {
            "old_password": "oldpassword123",
            "new_password1": "newpassword123",
            "new_password2": "newpassword123"
        }
        response = self.client.post(self.url, valid_data)
        # Expect a redirect (302) to employer_settings.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("employer_settings"))
        # Verify that a success message was added.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("successfully changed" in message.message for message in messages))
        # Logout and verify that the user can log in with the new password.
        self.client.logout()
        login_success = self.client.login(username="testuser", password="newpassword123")
        self.assertTrue(login_success)

    def test_post_invalid_change_password_incorrect_current(self):
        """Test that an incorrect current password re-renders the form with an error."""
        data = {
            "old_password": "wrongpassword",
            "new_password1": "newpassword123",
            "new_password2": "newpassword123"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "change_password.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("issue with your password change" in message.message for message in messages))

    def test_post_invalid_change_password_mismatch(self):
        """Test that mismatched new passwords re-render the form with an error."""
        data = {
            "old_password": "oldpassword123",
            "new_password1": "newpassword123",
            "new_password2": "differentpassword"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "change_password.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("issue with your password change" in message.message for message in messages))

    def test_post_invalid_change_password_too_short(self):
        """Test that a new password shorter than 8 characters re-renders the form with an error."""
        data = {
            "old_password": "oldpassword123",
            "new_password1": "short",
            "new_password2": "short"
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "change_password.html")
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("issue with your password change" in message.message for message in messages))

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
