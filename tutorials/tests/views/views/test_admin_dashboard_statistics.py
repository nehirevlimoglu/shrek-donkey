from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Job, Employer
from tutorials.models.admin_models import Admin
from django.utils import timezone
from datetime import timedelta
import json

User = get_user_model()

class AdminDashboardStatisticsTests(TestCase):
    """Test suite for admin dashboard statistics"""
    
    def setUp(self):
        """Set up test data for dashboard statistics tests"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            email='admin@test.com',
            role='Admin'
        )
        
        # Create jobs with different statuses
        self.pending_job1 = Job.objects.create(
            title="Pending Job 1",
            company_name="Company A",
            status="pending"
        )
        
        self.pending_job2 = Job.objects.create(
            title="Pending Job 2",
            company_name="Company B",
            status="pending"
        )
        
        self.approved_job1 = Job.objects.create(
            title="Approved Job 1",
            company_name="Company C",
            status="approved"
        )
        
        self.approved_job2 = Job.objects.create(
            title="Approved Job 2",
            company_name="Company D",
            status="approved"
        )
        
        self.rejected_job = Job.objects.create(
            title="Rejected Job",
            company_name="Company E",
            status="rejected"
        )
        
        # Set up test client and login as admin
        self.client = Client()
        self.client.login(username='testadmin', password='testpass123')
    
    def test_active_users_data(self):
        """Test active users data retrieval for different time periods"""
        # Create some users with different last login times
        for i in range(5):
            user = User.objects.create_user(
                username=f'testuser{i}',
                password='testpass123',
                email=f'user{i}@test.com'
            )
            # Set different last login times
            user.last_login = timezone.now() - timedelta(days=i)
            user.save()

        # Test daily data
        response = self.client.get(reverse('get_active_users_data'), {'period': 'day'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('values', data)
        self.assertEqual(len(data['labels']), 7)  # 7 days
        self.assertEqual(len(data['values']), 7)

        # Test weekly data
        response = self.client.get(reverse('get_active_users_data'), {'period': 'week'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['labels']), 4)  # 4 weeks
        self.assertEqual(len(data['values']), 4)

        # Test monthly data
        response = self.client.get(reverse('get_active_users_data'), {'period': 'month'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['labels']), 12)  # 12 months
        self.assertEqual(len(data['values']), 12)

        # Test invalid period
        response = self.client.get(reverse('get_active_users_data'), {'period': 'invalid'})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data) 