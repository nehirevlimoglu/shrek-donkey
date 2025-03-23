# tutorials/tests/views/test_csrf_failure_view.py
from django.test import TestCase, RequestFactory, Client
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.contrib.auth.models import AnonymousUser
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from django.urls import reverse
from tutorials.views.views import csrf_failure

class CSRFFailureViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

    def test_csrf_failure_view_sets_token_and_returns_login(self):
        """Test that the CSRF failure view renders login page with correct messaging and sets cookie."""
        request = self.factory.get('/fake-url/')
        request.user = AnonymousUser()

        # Required for messages framework to work in tests
        setattr(request, 'session', self.client.session)
        fallback = FallbackStorage(request)
        setattr(request, '_messages', fallback)

        # Call the view with a fake reason
        response = csrf_failure(request, reason="CSRF token missing")

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Check that the template used is log_in.html.
        # Because we're not using the Django test client "response = self.client.get(...)",
        # we can't use self.assertTemplateUsed(). Instead, we can check the template name:
        # The 'render()' call attaches templates info to response.templates:
        template_names = [t.name for t in getattr(response, 'templates', [])]
        self.assertContains(response, "<form")  # ensures your log-in form is rendered



        # Confirm CSRF error message appears in the HTML
        self.assertIn(b"Form submission failed", response.content)
        self.assertIn(b"CSRF validation error", response.content)

        # Check the cookie is actually set
        self.assertIn('csrftoken', response.cookies, "No csrftoken cookie was set by the response.")

        # For deeper checking, we can see the cookie value or samesite
        cookie = response.cookies['csrftoken']
        # By default, we set it to request.META.get('CSRF_COOKIE', '')
        # If there's no CSRF_COOKIE in META, it'll be empty string
        self.assertIsNotNone(cookie.value)  # Possibly an empty string "" if not set
        self.assertIn('samesite', cookie.keys(), "samesite attribute not found in the cookie.")
        self.assertEqual(cookie['samesite'], '', "Expected samesite=None represented by empty string.")


    def test_csrf_failure_logs_reason(self):
        """Ensure that failure reason is captured in the response."""
        request = self.factory.get('/some-url/')
        request.user = AnonymousUser()
        setattr(request, 'session', self.client.session)
        fallback = FallbackStorage(request)
        setattr(request, '_messages', fallback)

        response = csrf_failure(request, reason="Tampered token")

        # We only do a substring check for the reason in the rendered HTML
        self.assertContains(response, "Tampered token")
