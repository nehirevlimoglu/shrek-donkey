from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from tutorials.models.applicants_models import Applicant

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
            degree="bachelors",
            salary_preferences="50000",
            location_preferences="Local",
        )
        self.url = reverse("applicants-account")

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        login_url = reverse("log_in")
        expected_redirect = f"{login_url}?next={self.url}"
        self.assertRedirects(response, expected_redirect)

    def test_default_tab_profile(self):
        self.client.login(username="applicantuser", password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        self.assertEqual(response.context["tab"], "profile")
        self.assertIsNone(response.context["form"])

    def test_get_edit_profile_tab(self):
        self.client.login(username="applicantuser", password="Password123")
        response = self.client.get(f"{self.url}?tab=edit_profile")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        self.assertEqual(response.context["tab"], "edit_profile")
        self.assertIsNotNone(response.context["form"])

    def test_post_edit_profile_success(self):
        self.client.login(username="applicantuser", password="Password123")
        valid_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@smith.com",  # ✅ Add this line
            "degree": "masters",
            "salary_preferences": "60000",
            "location_preferences": "Remote",
        }

        response = self.client.post(f"{self.url}?tab=edit_profile", valid_data)
        self.assertRedirects(response, self.url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.last_name, "Smith")


    def test_post_edit_profile_failure(self):
        self.client.login(username="applicantuser", password="Password123")
        invalid_data = {
            "first_name": "Test",
            "last_name": "User",
            "degree": "x" * 300,  # Exceeds max_length
            "salary_preferences": "50000",
            "location_preferences": "Remote",
        }
        response = self.client.post(f"{self.url}?tab=edit_profile", invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        self.assertIsNotNone(response.context["form"])
        form = response.context["form"]
        self.assertTrue(form.errors)

    def test_get_password_tab(self):
        self.client.login(username="applicantuser", password="Password123")
        response = self.client.get(f"{self.url}?tab=password")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_account.html")
        self.assertEqual(response.context["tab"], "password")
        self.assertIsNotNone(response.context["form"])

    def test_post_password_change_success(self):
        self.client.login(username="applicantuser", password="Password123")
        valid_pw_data = {
            "old_password": "Password123",
            "new_password1": "NewPass456",
            "new_password2": "NewPass456",
        }
        response = self.client.post(f"{self.url}?tab=password", valid_pw_data)
        self.assertRedirects(response, self.url)

        msgs = list(get_messages(response.wsgi_request))
        self.assertTrue(any("password changed successfully" in m.message.lower() for m in msgs))

        self.client.logout()
        login_success = self.client.login(username="applicantuser", password="NewPass456")
        self.assertTrue(login_success)

    def test_post_password_change_failure(self):
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
        self.assertTrue(response.context["form"].errors)

        self.client.logout()
        login_success = self.client.login(username="applicantuser", password="NewPass456")
        self.assertFalse(login_success)
