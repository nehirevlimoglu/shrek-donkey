from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification
from django.utils import timezone

User = get_user_model()

class AdminNotificationsTests(TestCase):
    """Test suite for admin notifications functionality"""
    
    def setUp(self):
        """Set up test data for notifications tests"""
        # Create admin user with test credentials
        self.admin_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            email='admin@test.com',
            role='Admin'
        )
        
        # Create an unread notification for testing
        # This notification has high priority and job type
        self.unread_notification = Notification.objects.create(
            recipient=self.admin_user,
            title="Unread Job Notification",
            message="This is an unread notification",
            notification_type='job',
            priority='high',
            is_read=False
        )
        
        # Create a read notification for testing
        # This notification has low priority and system type
        self.read_notification = Notification.objects.create(
            recipient=self.admin_user,
            title="Read System Notification",
            message="This is a read notification",
            notification_type='system',
            priority='low',
            is_read=True
        )
        
        # Initialize test client
        self.client = Client()
        # Log in as admin user
        self.client.login(username='testadmin', password='testpass123')
    
    def test_notifications_page_load(self):
        """Test if notifications page loads correctly with filters"""
        # Make GET request to notifications page
        response = self.client.get(reverse('admin_notifications'))
        # Verify successful response
        self.assertEqual(response.status_code, 200)
        # Verify correct template is used
        self.assertTemplateUsed(response, 'admin_notifications.html')
        
        # Verify context data is correct
        # Check total notifications count
        self.assertEqual(response.context['total_count'], 2)
        # Check unread notifications count
        self.assertEqual(response.context['unread_count'], 1)
        # Check number of notifications returned
        self.assertEqual(len(response.context['notifications']), 2)

    def test_notification_filtering(self):
        """Test notification filtering functionality"""
        # Test filtering by notification type
        response = self.client.get(reverse('admin_notifications') + '?type=job')
        self.assertEqual(len(response.context['notifications']), 1)
        self.assertEqual(response.context['notifications'][0], self.unread_notification)

        # Test filtering by priority level
        response = self.client.get(reverse('admin_notifications') + '?priority=high')
        self.assertEqual(len(response.context['notifications']), 1)
        
        # Test filtering by read status
        response = self.client.get(reverse('admin_notifications') + '?is_read=unread')
        self.assertEqual(len(response.context['notifications']), 1)

    def test_mark_notification_as_read(self):
        """Test marking a notification as read"""
        # Make POST request to mark notification as read
        response = self.client.post(
            reverse('mark_notification_as_read', args=[self.unread_notification.id])
        )
        # Verify successful response
        self.assertEqual(response.status_code, 200)
        # Refresh notification from database
        self.unread_notification.refresh_from_db()
        # Verify notification is now marked as read
        self.assertTrue(self.unread_notification.is_read)

    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read"""
        # Make POST request to mark all notifications as read
        response = self.client.post(reverse('mark_all_notifications_as_read'))
        # Verify successful response
        self.assertEqual(response.status_code, 200)
        # Count remaining unread notifications
        unread_count = Notification.objects.filter(
            recipient=self.admin_user,
            is_read=False
        ).count()
        # Verify no unread notifications remain
        self.assertEqual(unread_count, 0)

    def test_delete_notification(self):
        """Test soft deleting a notification"""
        # Make POST request to delete notification
        response = self.client.post(
            reverse('delete_notification', args=[self.unread_notification.id])
        )
        # Verify successful response
        self.assertEqual(response.status_code, 200)
        # Refresh notification from database
        self.unread_notification.refresh_from_db()
        # Verify notification is marked as deleted
        self.assertTrue(self.unread_notification.is_deleted)

    def test_notification_creation(self):
        """Test notification creation utility function"""
        # Import notification creation function
        from tutorials.views.admin_views import create_admin_notification
        
        # Create a test notification
        create_admin_notification(
            user=self.admin_user,
            title="Test Notification",
            message="Test message",
            notification_type='job',
            priority='high'
        )
        
        # Retrieve the created notification
        notification = Notification.objects.get(title="Test Notification")
        # Verify notification recipient
        self.assertEqual(notification.recipient, self.admin_user)
        # Verify notification type
        self.assertEqual(notification.notification_type, 'job')
        # Verify notification priority
        self.assertEqual(notification.priority, 'high') 