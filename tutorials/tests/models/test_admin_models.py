from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.messages import get_messages
from django.db import IntegrityError

from tutorials.models.admin_models import Admin, Notification, NotificationPreference
from tutorials.models.user_model import User
from tutorials.models.employer_models import Job, Candidate, Interview, Employer, JobTitle
from django.contrib.auth import get_user_model
# Import Application if needed for related tests
# from tutorials.models.applicants_models import Application

User = get_user_model()

class AdminModelTest(TestCase):
    """Test cases for the Admin model."""
    
    def setUp(self):
        # Create an admin user using the User model's create_user
        self.user = User.objects.create_user(
            username='@testadmin',
            email='testadmin@example.com',
            password='password123',
            role='Admin'
        )
        # Create the Admin instance with the required user field.
        self.admin = Admin.objects.create(
            user=self.user,
            username='@testadmin',
            email='testadmin@example.com',
            first_name='Test',
            last_name='Admin',
            phone_number='+1234567890'
        )
    
    def test_admin_creation(self):
        """Ensure an Admin instance is created with correct attributes."""
        self.assertEqual(self.admin.username, '@testadmin')
        self.assertEqual(self.admin.email, 'testadmin@example.com')
        self.assertEqual(self.admin.first_name, 'Test')
        self.assertEqual(self.admin.last_name, 'Admin')
        self.assertEqual(self.admin.phone_number, '+1234567890')
        # Use the User method to check the password:
        self.assertTrue(self.user.check_password('password123'))
    
    def test_admin_str_method(self):
        """Test the string representation of the Admin model."""
        self.assertEqual(str(self.admin), '@testadmin')
    
    def test_admin_phone_validator(self):
        """Test the phone number validator on the Admin model."""
        # Set an invalid phone number
        self.admin.phone_number = 'invalid'
        with self.assertRaises(ValidationError):
            self.admin.full_clean()
        
        # Set a valid phone number
        self.admin.phone_number = '+9876543210'
        # Should not raise
        self.admin.full_clean()


class NotificationModelTest(TestCase):
    """Test cases for the Notification model."""
    
    def setUp(self):
        # Create an admin user and Admin instance.
        self.user = User.objects.create_user(
            username='testadmin',
            email='testadmin@example.com',
            password='password123',
            role='Admin'
        )
        self.admin = Admin.objects.create(
            user=self.user,
            username='testadmin',
            email='testadmin@example.com'
        )
        # Create a NotificationPreference instance (if used).
        self.notification_pref, created = NotificationPreference.objects.get_or_create(
            admin=self.admin,
            defaults={
                'job_notifications': True,
                'application_notifications': True,
                'user_notifications': False,
                'system_notifications': True,
                'email_delivery': True,
                'dashboard_delivery': False,
            }
        )
        # Create a Notification instance.
        self.notification = Notification.objects.create(
            recipient=self.user,
            title='Test Notification',
            message='This is a test notification.',
            notification_type=Notification.TYPE_GENERAL,
            priority=Notification.PRIORITY_MEDIUM,
            is_read=False
        )
    
    def test_notification_creation(self):
        """Ensure a Notification instance is created with the correct attributes."""
        self.assertEqual(self.notification.recipient, self.user)
        self.assertEqual(self.notification.title, 'Test Notification')
        self.assertEqual(self.notification.message, 'This is a test notification.')
        self.assertEqual(self.notification.notification_type, Notification.TYPE_GENERAL)
        self.assertEqual(self.notification.priority, Notification.PRIORITY_MEDIUM)
        self.assertFalse(self.notification.is_read)
        self.assertIsNotNone(self.notification.created_at)
    
    def test_notification_str_method(self):
        """Test the string representation of the Notification model."""
        expected_str = f"Test Notification - {self.user.username}"
        self.assertEqual(str(self.notification), expected_str)
    
    def test_mark_as_read(self):
        """Test that mark_as_read() correctly updates the is_read flag."""
        self.assertFalse(self.notification.is_read)
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)
    
    def test_soft_delete(self):
        """Test that soft_delete() correctly updates the is_deleted flag."""
        self.assertFalse(self.notification.is_deleted)
        self.notification.soft_delete()
        self.assertTrue(self.notification.is_deleted)
    
    def test_notification_ordering(self):
        """Ensure notifications are ordered by created_at in descending order."""
        # Create a newer notification.
        newer_notification = Notification.objects.create(
            recipient=self.user,
            title='Newer Notification',
            message='This is a newer notification.',
            notification_type=Notification.TYPE_GENERAL,
            priority=Notification.PRIORITY_MEDIUM,
            is_read=False
        )
        # Create an older notification.
        older_notification = Notification.objects.create(
            recipient=self.user,
            title='Older Notification',
            message='This is an older notification.',
            notification_type=Notification.TYPE_GENERAL,
            priority=Notification.PRIORITY_MEDIUM,
            is_read=False,
            created_at=timezone.now() - timedelta(days=1)
        )
        notifications = list(Notification.objects.all())
        self.assertEqual(notifications[0], newer_notification)
        self.assertEqual(notifications[1], self.notification)
        self.assertEqual(notifications[2], older_notification)


class NotificationPreferenceModelTest(TestCase):
    """Test cases for the NotificationPreference model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='@testadmin',
            email='testadmin@example.com',
            password='password123',
            role='Admin'
        )
        self.admin = Admin.objects.create(
            user=self.user,
            username='@testadmin',
            email='testadmin@example.com'
        )
        self.notification_pref, created = NotificationPreference.objects.get_or_create(
            admin=self.admin,
            defaults={
                'job_notifications': True,
                'application_notifications': True,
                'user_notifications': False,
                'system_notifications': True,
                'email_delivery': True,
                'dashboard_delivery': False,
            }
        )
        if not created:
            self.notification_pref.job_notifications = True
            self.notification_pref.application_notifications = True
            self.notification_pref.user_notifications = False
            self.notification_pref.system_notifications = True
            self.notification_pref.email_delivery = True
            self.notification_pref.dashboard_delivery = False
            self.notification_pref.save()
    
    def test_notification_preference_creation(self):
        """Ensure a NotificationPreference instance is created with the correct attributes."""
        self.assertEqual(self.notification_pref.admin, self.admin)
        self.assertTrue(self.notification_pref.job_notifications)
        self.assertTrue(self.notification_pref.application_notifications)
        self.assertFalse(self.notification_pref.user_notifications)
        self.assertTrue(self.notification_pref.system_notifications)
        self.assertTrue(self.notification_pref.email_delivery)
        self.assertFalse(self.notification_pref.dashboard_delivery)
        self.assertIsNotNone(self.notification_pref.last_updated)
    
    def test_notification_preference_str_method(self):
        """Test the string representation of the NotificationPreference model."""
        expected_str = f"Notification Preferences for {self.admin.username}"
        self.assertEqual(str(self.notification_pref), expected_str)
    
    def test_notification_preference_update(self):
        """Test that updates to NotificationPreference are saved correctly."""
        old_updated = self.notification_pref.last_updated
        
        self.notification_pref.job_notifications = False
        self.notification_pref.application_notifications = False
        self.notification_pref.user_notifications = True
        self.notification_pref.system_notifications = False
        self.notification_pref.email_delivery = False
        self.notification_pref.dashboard_delivery = True
        self.notification_pref.save()
        
        self.notification_pref.refresh_from_db()
        
        self.assertFalse(self.notification_pref.job_notifications)
        self.assertFalse(self.notification_pref.application_notifications)
        self.assertTrue(self.notification_pref.user_notifications)
        self.assertFalse(self.notification_pref.system_notifications)
        self.assertFalse(self.notification_pref.email_delivery)
        self.assertTrue(self.notification_pref.dashboard_delivery)
        self.assertGreater(self.notification_pref.last_updated, old_updated)
