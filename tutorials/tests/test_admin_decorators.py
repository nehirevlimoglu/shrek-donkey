from django.test import TestCase, RequestFactory
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.decorators import user_passes_test
from tutorials.models.admin_models import Admin
from tutorials.models.user_model import User
from tutorials.views.admin_views import is_admin, admin_home_page
from decorators import admin_only
from django.http import HttpResponse

class TestAdminDecorators(TestCase):
    """Test cases for admin decorators"""
    
    def setUp(self):
        """Set up test data for admin decorators tests"""
        # Create admin user
        self.admin_user = Admin.objects.create_user(
            username='testadmin',
            email='testadmin@example.com',
            password='password123',
            first_name='Test',
            last_name='Admin',
            role='Admin'
        )
        
        # Create non-admin user
        self.non_admin_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            role='Applicant'
        )
        
        # Set up request factory
        self.factory = RequestFactory()
    
    def test_is_admin_function(self):
        """Test is_admin function that checks if a user has the Admin role"""
        # Admin user should return True
        self.assertTrue(is_admin(self.admin_user))
        
        # Non-admin user should return False
        self.assertFalse(is_admin(self.non_admin_user))
    
    def test_user_passes_test_decorator(self):
        """Test user_passes_test decorator with is_admin function"""
        # Create a simple view function
        def test_view(request):
            return HttpResponse("Test view")
        
        # Apply the user_passes_test decorator
        decorated_view = user_passes_test(is_admin)(test_view)
        
        # Create a request with admin user
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        # Admin user should be able to access the view
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Create a request with non-admin user
        request = self.factory.get('/test/')
        request.user = self.non_admin_user
        
        # Non-admin user should be redirected to login page
        response = decorated_view(request)
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Anonymous user should also be redirected
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        response = decorated_view(request)
        self.assertEqual(response.status_code, 302)
    
    def test_admin_only_decorator(self):
        """Test admin_only decorator"""
        # Create a simple view function
        def test_view(request):
            return HttpResponse("Admin only view")
        
        # Apply the admin_only decorator
        decorated_view = admin_only(test_view)
        
        # Create a request with admin user
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        # Admin user should be able to access the view
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Create a request with non-admin user
        request = self.factory.get('/test/')
        request.user = self.non_admin_user
        
        # Non-admin user should get a 404 error
        with self.assertRaises(Http404):
            decorated_view(request)
    
    def test_admin_view_integration(self):
        """Test the integration with a real admin view"""
        # Login as admin user
        self.client.login(username='testadmin', password='password123')
        
        # Admin user should be able to access admin home page
        response = self.client.get(reverse('admin_home_page'))
        self.assertEqual(response.status_code, 200)
        
        # Logout and login as non-admin user
        self.client.logout()
        self.client.login(username='testuser', password='password123')
        
        # Non-admin user should not be able to access admin home page
        response = self.client.get(reverse('admin_home_page'))
        self.assertNotEqual(response.status_code, 200)
        
        # Anonymous user should not be able to access admin home page
        self.client.logout()
        response = self.client.get(reverse('admin_home_page'))
        self.assertNotEqual(response.status_code, 200) 