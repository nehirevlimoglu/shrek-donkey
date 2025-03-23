from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class LogOutViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='@testuser',
            email='testuser@example.com',
            password='testpass123',
            role='Applicant'
        )
        self.logout_url = reverse('log-out')
        self.login_url = reverse('log_in')

    def test_user_is_logged_out_and_redirected(self):
        """User is logged out and redirected to login page"""

        # First login the user
        self.client.login(username='@testuser', password='testpass123')

        # Ensure user is logged in
        response = self.client.get('/')  # Check any page requiring login
        self.assertEqual(str(response.wsgi_request.user), '@testuser')

        # Now logout
        response = self.client.get(self.logout_url)

        # Ensure user is logged out
        response_after_logout = self.client.get('/')  # Check page again
        self.assertFalse(response_after_logout.wsgi_request.user.is_authenticated)

        # Ensure redirected to login page
        self.assertRedirects(response, self.login_url)

        # Check CSRF cookie is deleted
        self.assertIn('csrftoken', response.cookies)
        self.assertEqual(response.cookies['csrftoken'].value, '')
        self.assertTrue(response.cookies['csrftoken']['max-age'] == 0)

    def test_logout_works_even_if_user_not_logged_in(self):
        """Logging out should gracefully redirect even if user isn't logged in"""

        response = self.client.get(self.logout_url)

        # Redirect to login page still expected
        self.assertRedirects(response, self.login_url)

        # Ensure no user is authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)

        # Check cookie deletion
        self.assertIn('csrftoken', response.cookies)
        self.assertEqual(response.cookies['csrftoken'].value, '')
        self.assertTrue(response.cookies['csrftoken']['max-age'] == 0)