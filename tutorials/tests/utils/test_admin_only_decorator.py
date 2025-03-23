# tutorials/tests/utils/test_admin_only_decorator.py

from django.test import TestCase, RequestFactory
from django.http import Http404, HttpResponse
from django.contrib.auth import get_user_model

from functools import wraps
from django.http import Http404

User = get_user_model()

# 1. The actual decorator inlined here for clarity, but you can import it from your code.
def admin_only(view_func):
    """Admin only access."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.role != "Admin":
            raise Http404("You are not authorized to view this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# 2. A dummy view that uses the decorator
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

        # Create a non-admin user (different email)
        self.regular_user = User.objects.create_user(
            username="regularuser",
            password="testpass",
            email="regular@example.org",
            role="Employee"
        )

    def test_admin_only_allows_admin_user(self):
        """
        The view should allow access if user.role == 'Admin'
        by returning status code 200 and 'Hello, Admin!' content.
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
