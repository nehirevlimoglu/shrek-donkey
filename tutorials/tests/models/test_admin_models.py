from django.test import TestCase
from django.core.exceptions import ValidationError
from tutorials.models.admin_models import Admin, Notification, NotificationPreference
from tutorials.models.user_model import User
from django.utils import timezone
from datetime import timedelta

class AdminModelTest(TestCase):
    """Test cases for Admin model"""
    
    def setUp(self):
        """Set up test data for Admin model tests"""
        self.admin = Admin.objects.create_user(
            username='testadmin',
            email='testadmin@example.com',
            password='password123',
            first_name='Test',
            last_name='Admin',
            role='Admin',
            phone_number='+1234567890'
        )
    
    def test_admin_creation(self):
        """Test that an Admin instance can be created correctly"""
        self.assertEqual(self.admin.username, 'testadmin')
        self.assertEqual(self.admin.email, 'testadmin@example.com')
        self.assertEqual(self.admin.first_name, 'Test')
        self.assertEqual(self.admin.last_name, 'Admin')
        self.assertEqual(self.admin.role, 'Admin')
        self.assertEqual(self.admin.phone_number, '+1234567890')
        self.assertTrue(self.admin.check_password('password123'))
    
    def test_admin_str_method(self):
        """Test the string representation of Admin model"""
        self.assertEqual(str(self.admin), 'testadmin')
    
    def test_admin_phone_validator(self):
        """Test phone number validation for Admin model"""
        # Test invalid phone number
        with self.assertRaises(ValidationError):
            self.admin.phone_number = 'invalid'
            self.admin.full_clean()
        
        # Test valid phone number
        self.admin.phone_number = '+9876543210'
        self.admin.full_clean()  # Should not raise ValidationError


class NotificationModelTest(TestCase):
    """Test cases for Notification model"""
    
    def setUp(self):
        """Set up test data for Notification model tests"""
        self.admin = Admin.objects.create_user(
            username='testadmin',
            email='testadmin@example.com',
            password='password123',
            role='Admin'
        )
        
        self.notification = Notification.objects.create(
            recipient=self.admin,
            title='Test Notification',
            message='This is a test notification.',
            notification_type=Notification.TYPE_GENERAL,
            priority=Notification.PRIORITY_MEDIUM,
            is_read=False
        )
    
    def test_notification_creation(self):
        """Test that a Notification instance can be created correctly"""
        self.assertEqual(self.notification.recipient, self.admin)
        self.assertEqual(self.notification.title, 'Test Notification')
        self.assertEqual(self.notification.message, 'This is a test notification.')
        self.assertEqual(self.notification.notification_type, Notification.TYPE_GENERAL)
        self.assertEqual(self.notification.priority, Notification.PRIORITY_MEDIUM)
        self.assertFalse(self.notification.is_read)
        self.assertIsNotNone(self.notification.created_at)
    
    def test_notification_str_method(self):
        """Test the string representation of Notification model"""
        expected_str = f"Test Notification - testadmin"
        self.assertEqual(str(self.notification), expected_str)
    
    def test_mark_as_read(self):
        """Test the mark_as_read method"""
        self.assertFalse(self.notification.is_read)
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)
    
    def test_soft_delete(self):
        """Test the soft_delete method"""
        self.assertFalse(self.notification.is_deleted)
        self.notification.soft_delete()
        self.assertTrue(self.notification.is_deleted)
    
    def test_notification_ordering(self):
        """Test that notifications are ordered by created_at in descending order"""
        # Create a newer notification
        newer_notification = Notification.objects.create(
            recipient=self.admin,
            title='Newer Notification',
            message='This is a newer notification.',
            notification_type=Notification.TYPE_GENERAL,
            priority=Notification.PRIORITY_MEDIUM,
            is_read=False
        )
        
        # Create an older notification
        older_notification = Notification.objects.create(
            recipient=self.admin,
            title='Older Notification',
            message='This is an older notification.',
            notification_type=Notification.TYPE_GENERAL,
            priority=Notification.PRIORITY_MEDIUM,
            is_read=False,
            created_at=timezone.now() - timedelta(days=1)
        )
        
        # Get all notifications ordered by created_at (default ordering)
        notifications = Notification.objects.all()
        
        # The newest notification should be first
        self.assertEqual(notifications[0], newer_notification)
        self.assertEqual(notifications[1], self.notification)
        self.assertEqual(notifications[2], older_notification)


class NotificationPreferenceModelTest(TestCase):
    """Test cases for NotificationPreference model"""
    
    def setUp(self):
        """Set up test data for NotificationPreference model tests"""
        self.admin = Admin.objects.create_user(
            username='testadmin',
            email='testadmin@example.com',
            password='password123',
            role='Admin'
        )
        
        self.notification_pref = NotificationPreference.objects.create(
            admin=self.admin,
            job_notifications=True,
            application_notifications=True,
            user_notifications=False,
            system_notifications=True,
            email_delivery=True,
            dashboard_delivery=False
        )
    
    def test_notification_preference_creation(self):
        """Test that a NotificationPreference instance can be created correctly"""
        self.assertEqual(self.notification_pref.admin, self.admin)
        self.assertTrue(self.notification_pref.job_notifications)
        self.assertTrue(self.notification_pref.application_notifications)
        self.assertFalse(self.notification_pref.user_notifications)
        self.assertTrue(self.notification_pref.system_notifications)
        self.assertTrue(self.notification_pref.email_delivery)
        self.assertFalse(self.notification_pref.dashboard_delivery)
        self.assertIsNotNone(self.notification_pref.last_updated)
    
    def test_notification_preference_str_method(self):
        """Test the string representation of NotificationPreference model"""
        expected_str = f"Notification Preferences for testadmin"
        self.assertEqual(str(self.notification_pref), expected_str)
    
    def test_notification_preference_update(self):
        """Test updating NotificationPreference"""
        old_updated = self.notification_pref.last_updated
        
        # Update preferences
        self.notification_pref.job_notifications = False
        self.notification_pref.application_notifications = False
        self.notification_pref.user_notifications = True
        self.notification_pref.system_notifications = False
        self.notification_pref.email_delivery = False
        self.notification_pref.dashboard_delivery = True
        self.notification_pref.save()
        
        # Refresh from database
        self.notification_pref.refresh_from_db()
        
        # Check updated values
        self.assertFalse(self.notification_pref.job_notifications)
        self.assertFalse(self.notification_pref.application_notifications)
        self.assertTrue(self.notification_pref.user_notifications)
        self.assertFalse(self.notification_pref.system_notifications)
        self.assertFalse(self.notification_pref.email_delivery)
        self.assertTrue(self.notification_pref.dashboard_delivery)
        
        # Check that last_updated was updated
        self.assertGreater(self.notification_pref.last_updated, old_updated) 