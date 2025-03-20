from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Admin, Notification

User = get_user_model()

class AdminDashboardTests(TestCase):
    def test_template_inheritance(self):
        """Check if templates correctly inherit from base templates."""
        response = self.client.get(reverse('admin_home_page'))
        self.assertContains(response, '{% extends')
        self.assertContains(response, 'admin_base.html')

    def test_notification_mark_as_read(self):
        """Test marking a notification as read updates the database."""
        unread_notification = Notification.objects.filter(is_read=False).first()
        self.assertIsNotNone(unread_notification)
        unread_notification.is_read = True
        unread_notification.save()
        self.assertTrue(Notification.objects.get(id=unread_notification.id).is_read)

    def test_invalid_url_returns_404(self):
        """Check if accessing an invalid URL returns a 404 status code."""
        response = self.client.get('/invalid-url/')
        self.assertEqual(response.status_code, 404)

    def test_context_data_integrity(self):
        """Ensure context data passed to template matches the database values."""
        response = self.client.get(reverse('admin_home_page'))
        admins_in_context = response.context['admins']
        db_admins = Admin.objects.all()
        self.assertQuerysetEqual(admins_in_context, db_admins, transform=lambda x: x)

    def test_csrf_token_in_forms(self):
        """Verify that CSRF tokens are present in all forms on the page."""
        response = self.client.get(reverse('admin_settings'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_post_request_security(self):
        """Ensure unauthorized POST requests are rejected."""
        response = self.client.post(reverse('admin_settings'), {})
        self.assertEqual(response.status_code, 403)
    """
    Comprehensive test cases for the Admin Dashboard in Django, including:
    - Template rendering
    - Context data validation
    - URL routing and status codes
    - Form submission and redirect tests
    - Edge cases and error handling
    """
    def setUp(self):
        """Setup initial data including test user, notifications, and client session."""

        self.user = User.objects.create_user(
            username='testadmin',
            password='testpassword',
            role='Admin'
        )
        self.client = Client()
        self.client.login(username='testadmin', password='testpassword')


        Notification.objects.create(
            recipient=self.user, 
            title='Test Notification 1',
            message='This is a test notification.',
            is_read=False
        )
        Notification.objects.create(
            recipient=self.user, 
            title='Test Notification 2',
            message='This is another test notification.',
            is_read=True
        )

    def test_admin_home_page(self):
        """Test if admin home page renders correctly with context data."""
        response = self.client.get(reverse('admin_home_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_home_page.html')
        self.assertContains(response, 'Welcome Back, testadmin')

    def test_admin_notifications_page(self):
        """Test if admin notifications page renders and displays notifications correctly."""
        response = self.client.get(reverse('admin_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_notifications.html')
        self.assertContains(response, 'Test Notification 1')
        self.assertContains(response, 'Test Notification 2')

    def test_unread_notification_count(self):
        """Test if unread notification count is displayed correctly in the template."""
        response = self.client.get(reverse('admin_notifications'))
        self.assertContains(response, '1') 

    def test_admin_job_listings_page(self):
        """Test if admin job listings page loads and uses the correct template."""
        response = self.client.get(reverse('admin_job_listings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_job_listings.html')

    def test_admin_settings_page(self):
        """Test if admin settings page loads and uses the correct template."""
        response = self.client.get(reverse('admin_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_settings.html')

    def test_logout(self):
        """Test if logout button correctly logs out and redirects to login page."""
        response = self.client.post(reverse('log-out'))
        self.assertEqual(response.status_code, 302) 
        self.assertRedirects(response, reverse('login'))
