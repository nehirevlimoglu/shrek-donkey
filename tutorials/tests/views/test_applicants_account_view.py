from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.messages import get_messages



from tutorials.models.applicants_models import Applicant
# Ensure these forms are imported if needed:
# from tutorials.forms.applicants_forms import ApplicantEditForm, CustomPasswordChangeForm

User = get_user_model()

class ApplicantsAccountViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="applicantuser",
            password="Password123",
            role="Applicant",
            email="applicant@example.org",
            first_name="John",
            last_name="Doe"
        )
        self.applicant = Applicant.objects.create(
            user=self.user,
            # ... include other required fields as needed ...
        )
        # The URL name is assumed to be "applicants-account"
        self.url = reverse("applicants-account")

    def test_redirect_if_not_logged_in(self):
        """If not logged in, the view should redirect to login."""
        response = self.client.get(self.url)
        login_url = reverse("log_in")
        expected_redirect = f"{login_url}?next={self.url}"
        self.assertRedirects(response, expected_redirect)

    def test_default_tab_profile(self):
        """
        GET with no tab parameter => default to 'profile'
        and no form in context.
        """
        self.client.login(username="applicantuser", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        self.assertEqual(response.context["tab"], "profile")
        self.assertIsNone(response.context["form"], "No form for profile tab")

    def test_get_edit_profile_tab(self):
        """
        GET with ?tab=edit_profile => returns ApplicantEditForm in context.
        """
        self.client.login(username="applicantuser", password="Password123")
        response = self.client.get(f"{self.url}?tab=edit_profile")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        self.assertEqual(response.context["tab"], "edit_profile")
        self.assertIsNotNone(response.context["form"], "Expected a profile form in context")

    def test_post_edit_profile_success(self):
        self.client.login(username="applicantuser", password="Password123")
        valid_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@smith.com",
        }
        response = self.client.post(f"{self.url}?tab=edit_profile", valid_data)
        self.assertRedirects(response, self.url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.last_name, "Smith")
        self.assertEqual(self.user.email, "alice@smith.com")

        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any("updated successfully" in m.message.lower() for m in msgs))

    def test_post_edit_profile_failure(self):
        self.client.login(username="applicantuser", password="Password123")
        invalid_data = {
            "first_name": "",  # required
            "last_name": "User",
            "email": "not-an-email",  # invalid
        }
        response = self.client.post(f"{self.url}?tab=edit_profile", invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        form = response.context["form"]
        self.assertTrue(form.errors)

    def test_get_password_tab(self):
        """
        GET with ?tab=password should return the CustomPasswordChangeForm in context.
        """
        self.client.login(username="applicantuser", password="Password123")
        response = self.client.get(f"{self.url}?tab=password")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        self.assertEqual(response.context["tab"], "password")
        self.assertIsNotNone(response.context["form"], "Expected a password form in context")

    def test_post_password_change_success(self):
        """
        POST valid password change data should change the password,
        set a success message, and redirect back to applicants-account.
        """
        self.client.login(username="applicantuser", password="Password123")
        valid_pw_data = {
            "old_password": "Password123",
            "new_password1": "NewPass456",
            "new_password2": "NewPass456",
        }
        response = self.client.post(f"{self.url}?tab=password", valid_pw_data)
        # The view returns redirect('applicants-account')
        self.assertRedirects(response, self.url)

        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any("password changed successfully" in m.message.lower() for m in msgs))

        # Confirm new password works
        self.client.logout()
        login_success = self.client.login(username="applicantuser", password="NewPass456")
        self.assertTrue(login_success, "Should log in with the new password after change")

    def test_post_password_change_failure(self):
        """
        POST invalid password data should re-render the page with errors, no redirect.
        """
        self.client.login(username="applicantuser", password="Password123")
        invalid_pw_data = {
            "old_password": "WrongOldPassword",
            "new_password1": "NewPass456",
            "new_password2": "NewPass456",
        }
        response = self.client.post(f"{self.url}?tab=password", invalid_pw_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        self.assertIsNotNone(response.context["form"])
        form = response.context["form"]
        self.assertTrue(form.errors, "Form should have errors for invalid password change")

        # Confirm that new password is not set.
        self.client.logout()
        login_success = self.client.login(username="applicantuser", password="NewPass456")
        self.assertFalse(login_success, "Should not log in with new password on failure")
