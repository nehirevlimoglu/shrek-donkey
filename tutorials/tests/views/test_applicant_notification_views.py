from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.applicants_models import Applicant, ApplicantNotification
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class ApplicantNotificationTests(TestCase):
    """Test suite for applicant notification functionality"""
    
    def setUp(self):
        """Set up test data for notification tests"""
        # Create applicant user
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )
        
        # Create another applicant user (to test notification isolation)
        self.other_applicant_user = User.objects.create_user(
            username='@otherapplicant',
            password='testpass123',
            email='other@test.com',
            first_name='Other',
            last_name='Applicant',
            role='Applicant'
        )
        
        # Create applicant profiles
        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            degree='Computer Science',
            salary_preferences='80000-100000',
            location_preferences='Remote'
        )
        
        self.other_applicant = Applicant.objects.create(
            user=self.other_applicant_user,
            degree='Data Science',
            salary_preferences='90000-110000',
            location_preferences='Hybrid'
        )
        
        # Create test notifications with different timestamps
        self.notifications = []
        for i in range(5):
            notification = ApplicantNotification.objects.create(
                applicant=self.applicant,
                title=f"Test Notification {i}",
                message=f"This is test notification {i}",
                is_read=False,
                timestamp=timezone.now() - timedelta(days=i)  # Different timestamps
            )
            self.notifications.append(notification)
            
        # Create notifications for other applicant
        self.other_notifications = []
        for i in range(3):
            notification = ApplicantNotification.objects.create(
                applicant=self.other_applicant,
                title=f"Other Notification {i}",
                message=f"This is other applicant's notification {i}",
                is_read=False
            )
            self.other_notifications.append(notification)
            
        # Set up test client and login
        self.client = Client()
        self.client.login(username='@testapplicant', password='testpass123')

    def test_view_notifications_authenticated(self):
        """Test viewing notifications when authenticated"""
        response = self.client.get(reverse('applicants-notifications'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_notifications.html')
        self.assertEqual(len(response.context['notifications']), 5)
        
        # Check notifications are ordered by timestamp (newest first)
        notifications = list(response.context['notifications'])
        self.assertTrue(all(
            notifications[i].timestamp >= notifications[i+1].timestamp 
            for i in range(len(notifications)-1)
        ))

    def test_notification_isolation(self):
        """Test that applicants can only see their own notifications"""
        response = self.client.get(reverse('applicants-notifications'))
        
        notifications = response.context['notifications']
        # Check no other applicant's notifications are visible
        self.assertTrue(all(
            notification.applicant.id == self.applicant.id 
            for notification in notifications
        ))
        # Verify other applicant's notifications are not included
        other_titles = [f"Other Notification {i}" for i in range(3)]
        self.assertTrue(all(
            notification.title not in other_titles 
            for notification in notifications
        ))

    def test_empty_notifications(self):
        """Test viewing notifications when none exist"""
        # Delete all notifications for the test applicant
        ApplicantNotification.objects.filter(applicant=self.applicant).delete()
        
        response = self.client.get(reverse('applicants-notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['notifications']), 0)

    def test_view_notifications_unauthenticated(self):
        """Test viewing notifications when not logged in"""
        self.client.logout()
        response = self.client.get(reverse('applicants-notifications'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, 
            f"{reverse('log_in')}?next={reverse('applicants-notifications')}"
        )

    def test_non_applicant_access(self):
        """Test that non-applicants cannot access notifications"""
        # Create and login as non-applicant user
        non_applicant = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            role='Employer'
        )
        self.client.login(username='@testemployer', password='testpass123')
        
        response = self.client.get(reverse('applicants-notifications'))
        self.assertEqual(response.status_code, 403)

    def test_notification_timestamp_ordering(self):
        """Test notifications are properly ordered by timestamp"""
        response = self.client.get(reverse('applicants-notifications'))
        notifications = list(response.context['notifications'])
        
        # Verify descending order
        timestamps = [notification.timestamp for notification in notifications]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_applicant_switch(self):
        """Test switching between applicant accounts"""
        # First check original applicant's notifications
        response = self.client.get(reverse('applicants-notifications'))
        self.assertEqual(len(response.context['notifications']), 5)
        
        # Switch to other applicant
        self.client.logout()
        self.client.login(username='@otherapplicant', password='testpass123')
        
        response = self.client.get(reverse('applicants-notifications'))
        self.assertEqual(len(response.context['notifications']), 3)
        # Verify correct notifications are shown
        self.assertTrue(all(
            "Other Notification" in notification.title 
            for notification in response.context['notifications']
        ))
