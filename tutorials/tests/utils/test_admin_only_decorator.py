# tutorials/tests/utils/test_admin_only_decorator.py

from django.test import TestCase, RequestFactory
from django.http import Http404, HttpResponse
from django.contrib.auth import get_user_model

# 1. Import your real decorator from `tutorials.decorators`
from tutorials.decorators import admin_only

User = get_user_model()

# 2. Define a dummy view that uses the REAL admin_only
@admin_only
def protected_admin_view(request):
    return HttpResponse("Hello, Admin!")

class AdminOnlyDecoratorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create a user with role Admin (unique email)
        self.admin_user = User.objects.create_user(
            username="adminuser",
            password="testpass",
            email="admin@example.org",
            role="Admin"
        )

        # Create a non-admin user
        self.regular_user = User.objects.create_user(
            username="regularuser",
            password="testpass",
            email="regular@example.org",
            role="Employee"
        )

    def test_admin_only_allows_admin_user(self):
        """
        The view should allow access if user.role == 'Admin'
        returning 200 and 'Hello, Admin!' content.
        """
        request = self.factory.get("/some-url/")
        request.user = self.admin_user
        response = protected_admin_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hello, Admin!")

    def test_admin_only_denies_non_admin_user(self):
        """
        The view should raise Http404 if user.role != 'Admin'.
        """
        request = self.factory.get("/some-url/")
        request.user = self.regular_user
        with self.assertRaises(Http404):
            protected_admin_view(request)
