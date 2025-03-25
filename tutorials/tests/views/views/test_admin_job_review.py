from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Job, Employer
from tutorials.models.admin_models import Admin
import json

User = get_user_model()

class AdminJobReviewTests(TestCase):
    """Test suite for admin job review functionality"""
    
    def setUp(self):
        """Set up test data for job review tests"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            email='admin@test.com',
            role='Admin'
        )
        
        # Create test jobs with different statuses
        self.pending_job = Job.objects.create(
            title="Pending Job",
            company_name="Test Company",
            location="Test Location",
            salary=50000,
            job_type="Full Time",
            status="pending"
        )
        
        # Set up test client and login as admin
        self.client = Client()
        self.client.login(username='testadmin', password='testpass123')
    
    def test_job_listings_view(self):
        """Test viewing job listings page"""
        response = self.client.get(reverse('admin_job_listings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_job_listings.html')
        self.assertIn('jobs', response.context)
    
    def test_update_job_status_approve(self):
        """Test approving a job"""
        data = {
            'job_id': self.pending_job.id,
            'status': 'approved'
        }
        response = self.client.post(
            reverse('update_job_status'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify job status was updated
        self.pending_job.refresh_from_db()
        self.assertEqual(self.pending_job.status, 'approved')
    
    def test_update_job_status_reject(self):
        """Test rejecting a job"""
        data = {
            'job_id': self.pending_job.id,
            'status': 'rejected'
        }
        response = self.client.post(
            reverse('update_job_status'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify job status was updated
        self.pending_job.refresh_from_db()
        self.assertEqual(self.pending_job.status, 'rejected')
    
    def test_invalid_job_id(self):
        """Test handling invalid job ID"""
        data = {
            'job_id': 9999,
            'status': 'approved'
        }
        response = self.client.post(
            reverse('update_job_status'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_status(self):
        """Test handling invalid status"""
        data = {
            'job_id': self.pending_job.id,
            'status': 'invalid_status'
        }
        response = self.client.post(
            reverse('update_job_status'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Check both the status code and response content
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data) 