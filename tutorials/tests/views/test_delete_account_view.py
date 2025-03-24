from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.models import AnonymousUser

from tutorials.models.employer_models import Employer

User = get_user_model()

class DeleteAccountViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an employer user with role "Employer"
        self.user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.user)
        # Create an Employer instance associated with this user.
        self.employer = Employer.objects.create(
            user=self.user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        self.url = reverse("delete_account")
        self.home_url = reverse("log_in")

    def test_get_delete_account_view(self):
        """Test that a GET request renders the delete account confirmation page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "delete_account.html")

    def test_post_delete_account_success(self):
        """Test that a valid POST deletes the Employer and User, logs out, and redirects to home_page."""
        # Perform POST request.
        response = self.client.post(self.url)
        # Expect a redirect to home_page.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        # Check that the Employer instance is deleted.
        self.assertFalse(Employer.objects.filter(user=self.user).exists())
        # Check that the User is deleted.
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        # Because the user is deleted, subsequent requests should have an AnonymousUser.
        response2 = self.client.get(self.home_url)
        self.assertEqual(response2.wsgi_request.user.__class__, AnonymousUser)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
