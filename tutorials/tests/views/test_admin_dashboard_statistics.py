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
        # Create admin user with valid username format
        self.admin_user = User.objects.create_user(
            username='@testadmin',
            password='testpass123',
            email='admin@test.com',
            first_name='Test',  # Add these required fields
            last_name='Admin',  # Add these required fields
            role='Admin'
        )
        
        # Create employer user with valid username format
        employer_user = User.objects.create_user(
            username='@employer',
            password='testpass123',
            email='employer@test.com',
            first_name='Test',  # Add these required fields
            last_name='Employer',  # Add these required fields
            role='Employer'
        )
        
        # Create employer
        self.employer = Employer.objects.create(
            user=employer_user,
            company_name='Test Company'
        )
        
        # Create jobs with different statuses
        self.pending_job1 = Job.objects.create(
            employer=self.employer,
            title="Pending Job 1",
            company_name="Company A",
            location="Test Location",
            description="Test Description",
            job_type="Full Time",  # Add required field
            status="pending"
        )
        
        self.pending_job2 = Job.objects.create(
            employer=self.employer,
            title="Pending Job 2",
            company_name="Company B",
            location="Test Location",
            description="Test Description",
            job_type="Full Time",  # Add required field
            status="pending"
        )
        
        self.approved_job1 = Job.objects.create(
            employer=self.employer,
            title="Approved Job 1",
            company_name="Company C",
            location="Test Location",
            description="Test Description",
            job_type="Full Time",  # Add required field
            status="approved"
        )
        
        self.approved_job2 = Job.objects.create(
            employer=self.employer,
            title="Approved Job 2",
            company_name="Company D",
            location="Test Location",
            description="Test Description",
            job_type="Full Time",  # Add required field
            status="approved"
        )
        
        self.rejected_job = Job.objects.create(
            employer=self.employer,
            title="Rejected Job",
            company_name="Company E",
            location="Test Location",
            description="Test Description",
            job_type="Full Time",  # Add required field
            status="rejected"
        )
        
        # Fix the login by using the correct username with @ symbol
        self.client = Client()
        logged_in = self.client.login(username='@testadmin', password='testpass123')
        if not logged_in:
            raise Exception("Failed to log in admin user")
    
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

        # Test daily data with error handling
        response = self.client.get(reverse('get_active_users_data'), {'period': 'day'})
        self.assertEqual(response.status_code, 200)
        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            print("Invalid JSON response:", response.content)
            raise
        
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

    def test_job_statistics(self):
        """Test job statistics calculations"""
        response = self.client.get(reverse('admin_home_page'))
        self.assertEqual(response.status_code, 200)
        
        # Test using the correct context variable names from admin_home_page view
        self.assertEqual(response.context['total_jobs'], 5)  # Total jobs (5 jobs created in setUp)
        self.assertEqual(response.context['pending_jobs'], 2)  # 2 pending jobs created in setUp
        self.assertEqual(response.context['approved_jobs'], 2)  # 2 approved jobs created in setUp
        self.assertEqual(response.context['rejected_jobs'], 1)  # 1 rejected job created in setUp

    def test_user_activity_trends(self):
        """Test user activity trend calculations"""
        # Reset admin and employer last_login to None so they aren't counted
        self.admin_user.last_login = None
        self.admin_user.save()
        
        today = timezone.now()
        
        # Create users with logins today
        for i in range(3):
            user = User.objects.create_user(
                username=f'today_user_{i}',
                password='testpass123',
                email=f'today{i}@test.com'
            )
            user.last_login = today
            user.save()
            
        # Create users with logins yesterday
        for i in range(2):
            user = User.objects.create_user(
                username=f'yesterday_user_{i}',
                password='testpass123',
                email=f'yesterday{i}@test.com'
            )
            user.last_login = today - timedelta(days=1)
            user.save()

        response = self.client.get(reverse('get_active_users_data'), {'period': 'day'})
        data = json.loads(response.content)
        
        # Update expected count to include admin user
        self.assertEqual(data['values'][-1], 3)  # Today's users (exactly 3)
        self.assertEqual(data['values'][-2], 2)  # Yesterday's users 