from django.test import TestCase, Client, RequestFactory
from django.middleware.csrf import CsrfViewMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.urls import reverse
from tutorials.views.views import csrf_failure


class CSRFFailureViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

    def test_csrf_failure_view_sets_token_and_returns_login(self):
        """Test that the CSRF failure view renders login page with correct messaging"""
        request = self.factory.get('/fake-url/')
        request.user = AnonymousUser()

        # Required for messages framework to work in tests
        setattr(request, 'session', self.client.session)
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Call the view with a fake reason
        response = csrf_failure(request, reason="CSRF token missing")

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Confirm CSRF error message appears in the HTML
        self.assertIn(b"Form submission failed", response.content)
        self.assertIn(b"CSRF validation error", response.content)

        # Optional: check for a piece of content specific to your login page
        self.assertIn(b"<form", response.content)  # Ensures form is present
        self.assertIn(b"username", response.content.lower())  # Common in login forms

    def test_csrf_failure_logs_reason(self):
        """Ensure that failure reason is captured and printed"""
        request = self.factory.get('/some-url/')
        request.user = AnonymousUser()
        setattr(request, 'session', self.client.session)
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # You can pass an alternate reason
        response = csrf_failure(request, reason="Tampered token")

        self.assertContains(response, "Tampered token")