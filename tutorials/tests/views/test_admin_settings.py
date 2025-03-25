from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Admin, NotificationPreference
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError

User = get_user_model()

class AdminSettingsTests(TestCase):
    """Test suite for admin settings functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user with correct role
        self.admin = Admin.objects.create_user(
            username='@testadmin',
            password='testpass123',
            email='admin@test.com',
            first_name='Test',
            last_name='Admin',
            role='Admin',
            phone_number='1234567890'
        )
        
        # Create another user for testing duplicate usernames
        self.other_user = User.objects.create_user(
            username='@otheruser',
            password='testpass123',
            email='other@test.com',
            role='User'
        )
        
        # Set up client and login
        self.client = Client()
        logged_in = self.client.login(username='@testadmin', password='testpass123')
        self.assertTrue(logged_in)  # Verify login was successful

    def test_settings_page_load(self):
        """Test if settings page loads correctly"""
        response = self.client.get(reverse('admin_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_settings.html')
        self.assertIn('user', response.context)
        self.assertIn('admin', response.context)

    

    def test_update_profile_duplicate_username(self):
        """Test profile update with duplicate username"""
        data = {
            'update_profile': True,
            'username': '@otheruser',  # Already exists
            'email': 'admin@test.com',
            'first_name': 'Test',
            'last_name': 'Admin',
            'phone_number': '1234567890'
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check that the form is re-rendered with error
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
        self.assertEqual(
            response.context['error'],
            "Username already exists. Please choose a different one."
        )
        
        # Verify user data was not updated
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.username, '@testadmin')

    

    def test_change_password_success(self):
        """Test successful password change"""
        data = {
            'change_password': True,
            'current_password': 'testpass123',
            'new_password': 'newtestpass123',
            'confirm_password': 'newtestpass123'
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_settings'))
        
        # Verify password was changed
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('newtestpass123'))
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Password changed successfully.")

    def test_change_password_incorrect_current(self):
        """Test password change with incorrect current password"""
        data = {
            'change_password': True,
            'current_password': 'wrongpass',
            'new_password': 'newtestpass123',
            'confirm_password': 'newtestpass123'
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check error
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], "Current password is incorrect.")
        self.assertEqual(response.context['tab'], 'password')

    
   

    def test_change_password_mismatch(self):
        """Test password change with mismatched new passwords"""
        data = {
            'change_password': True,
            'current_password': 'testpass123',
            'new_password': 'newtestpass123',
            'confirm_password': 'differentpass123'  # Doesn't match new_password
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check error message and tab
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], "New passwords do not match.")
        self.assertEqual(response.context['tab'], 'password')
        
        # Verify password was not changed
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('testpass123'))

    def test_change_password_too_short(self):
        """Test password change with password shorter than 8 characters"""
        data = {
            'change_password': True,
            'current_password': 'testpass123',
            'new_password': 'short',  # Less than 8 characters
            'confirm_password': 'short'
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check error message and tab
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], "Password must be at least 8 characters long.")
        self.assertEqual(response.context['tab'], 'password')
        
        # Verify password was not changed
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('testpass123'))

    def test_change_password_edge_cases(self):
        """Test password change with various edge cases"""
        test_cases = [
            {
                'name': 'empty_new_password',
                'data': {
                    'change_password': True,
                    'current_password': 'testpass123',
                    'new_password': '',
                    'confirm_password': ''
                },
                'expected_error': "Password must be at least 8 characters long.",
                'should_redirect': False
            },
            {
                'name': 'exactly_8_chars',
                'data': {
                    'change_password': True,
                    'current_password': 'testpass123',
                    'new_password': 'exactly8c',
                    'confirm_password': 'exactly8c'
                },
                'expected_error': None,
                'should_redirect': True
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(name=test_case['name']):
                # Get fresh admin object before each test case
                self.admin = Admin.objects.select_related('user_ptr').get(id=self.admin.id)
                original_password_hash = self.admin.password
                
                response = self.client.post(reverse('admin_settings'), test_case['data'])
                
                # Refresh admin object after the request
                self.admin = Admin.objects.select_related('user_ptr').get(id=self.admin.id)
                
                if test_case['expected_error']:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['error'], test_case['expected_error'])
                    self.assertEqual(response.context['tab'], 'password')
                    # Verify password hasn't changed
                    self.assertEqual(self.admin.password, original_password_hash)
                else:
                    self.assertRedirects(response, reverse('admin_settings'))
                    # Verify password has changed
                    self.assertNotEqual(self.admin.password, original_password_hash)
                    self.assertTrue(self.admin.check_password(test_case['data']['new_password']))

                # Re-login after password change if needed
                if test_case['should_redirect']:
                    self.client.login(
                        username=self.admin.username,
                        password=test_case['data']['new_password']
                    )



    def test_update_profile_admin_specific_fields(self):
        """Test updating admin-specific fields (phone number)"""
        data = {
            'update_profile': True,
            'username': '@testadmin',
            'email': 'admin@test.com',
            'first_name': 'Test',
            'last_name': 'Admin',
            'phone_number': '5555555555'  # only changing phone number
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_settings'))
        
        # Verify only admin-specific field was updated
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.phone_number, '5555555555')
        
        # Verify other fields remained unchanged
        self.assertEqual(self.admin.username, '@testadmin')
        self.assertEqual(self.admin.email, 'admin@test.com')
        self.assertEqual(self.admin.first_name, 'Test')
        self.assertEqual(self.admin.last_name, 'Admin')

    def test_notification_preferences_create(self):
        """Test creating new notification preferences when none exist"""
        # First delete any existing preferences
        NotificationPreference.objects.filter(admin=self.admin).delete()
        
        data = {
            'update_notification_prefs': True,
            'job_notifications': 'on',
            'application_notifications': 'on',
            'user_notifications': 'on',
            'system_notifications': 'on',
            'email_delivery': 'on',
            'dashboard_delivery': 'on'
        }
        
        # Verify no preferences exist yet
        self.assertFalse(NotificationPreference.objects.filter(admin=self.admin).exists())
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check redirect and success message
        self.assertRedirects(response, reverse('admin_settings'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Notification preferences updated successfully.")
        
        # Verify preferences were created
        prefs = NotificationPreference.objects.get(admin=self.admin)
        self.assertTrue(prefs.job_notifications)
        self.assertTrue(prefs.application_notifications)
        self.assertTrue(prefs.user_notifications)
        self.assertTrue(prefs.system_notifications)
        self.assertTrue(prefs.email_delivery)
        self.assertTrue(prefs.dashboard_delivery)

    def test_notification_preferences_update(self):
        """Test updating existing notification preferences"""
        # First delete any existing preferences
        NotificationPreference.objects.filter(admin=self.admin).delete()
        
        # Create initial preferences
        initial_prefs = NotificationPreference.objects.create(
            admin=self.admin,
            job_notifications=True,
            application_notifications=True,
            user_notifications=True,
            system_notifications=True,
            email_delivery=True,
            dashboard_delivery=True
        )
        
        # Update with some preferences turned off
        data = {
            'update_notification_prefs': True,
            'job_notifications': 'on',
            'system_notifications': 'on',
            'email_delivery': 'on'
            # Omitting others should set them to False
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check redirect and success message
        self.assertRedirects(response, reverse('admin_settings'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Notification preferences updated successfully.")
        
        # Verify preferences were updated
        prefs = NotificationPreference.objects.get(admin=self.admin)
        self.assertTrue(prefs.job_notifications)
        self.assertFalse(prefs.application_notifications)
        self.assertFalse(prefs.user_notifications)
        self.assertTrue(prefs.system_notifications)
        self.assertTrue(prefs.email_delivery)
        self.assertFalse(prefs.dashboard_delivery)

    def test_notification_preferences_all_disabled(self):
        """Test updating notification preferences with all options disabled"""
        # First delete any existing preferences
        NotificationPreference.objects.filter(admin=self.admin).delete()
        
        # Create initial preferences with everything enabled
        initial_prefs = NotificationPreference.objects.create(
            admin=self.admin,
            job_notifications=True,
            application_notifications=True,
            user_notifications=True,
            system_notifications=True,
            email_delivery=True,
            dashboard_delivery=True
        )
        
        # Submit update with no preferences selected
        data = {
            'update_notification_prefs': True
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check redirect and success message
        self.assertRedirects(response, reverse('admin_settings'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Notification preferences updated successfully.")
        
        # Verify all preferences are now False
        prefs = NotificationPreference.objects.get(admin=self.admin)
        self.assertFalse(prefs.job_notifications)
        self.assertFalse(prefs.application_notifications)
        self.assertFalse(prefs.user_notifications)
        self.assertFalse(prefs.system_notifications)
        self.assertFalse(prefs.email_delivery)
        self.assertFalse(prefs.dashboard_delivery)

    def test_session_maintained_after_password_change(self):
        """Test that user session is maintained after password change"""
        data = {
            'change_password': True,
            'current_password': 'testpass123',
            'new_password': 'newtestpass123',
            'confirm_password': 'newtestpass123'
        }
        
        response = self.client.post(reverse('admin_settings'), data)
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_settings'))
        
        # Verify user is still authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
        # Try accessing a protected page
        response = self.client.get(reverse('admin_settings'))
        self.assertEqual(response.status_code, 200) 