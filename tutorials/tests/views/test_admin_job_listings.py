from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tutorials.models.employer_models import Job, Employer, Candidate
from tutorials.models.admin_models import Admin
from datetime import timedelta
from django.db.models import Q
import json
import logging
from unittest.mock import patch

# Set up logger for tests
logger = logging.getLogger(__name__)

User = get_user_model()

class AdminJobListingsTests(TestCase):
    """Test suite for admin job listings functionality"""
    
    def setUp(self):
        """Set up test data for job listings tests"""
        # Create admin user - Admin model likely extends User
        self.admin_user = User.objects.create_user(
            username='@testadmin',
            password='testpass123',
            email='admin@test.com',
            role='Admin'  # Make sure role is set to Admin
        )
        
        # Create employer for test jobs
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            role='Employer'
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='Test Company'
        )
        
        # Create test jobs with different statuses and dates
        self.create_test_jobs()
        
        # Set up test client and login as admin with correct username
        self.client = Client()
        self.client.login(username='@testadmin', password='testpass123')

    def create_test_jobs(self):
        """Create test jobs with various statuses and deadlines"""
        # Job with no deadline (open)
        self.open_job_no_deadline = Job.objects.create(
            employer=self.employer,
            title="Open Position No Deadline",
            company_name="Test Company",
            location="Remote",
            description="Test job description",
            job_type="Full-time",
            application_deadline=None,
            created_at=timezone.now()
        )
        
        # Job with future deadline (open)
        self.open_job = Job.objects.create(
            employer=self.employer,
            title="Open Position",
            company_name="Tech Corp",
            location="New York",
            description="Test job description",
            job_type="Full-time",
            application_deadline=timezone.now().date() + timedelta(days=30),
            created_at=timezone.now() - timedelta(days=5)
        )
        
        # Job with past deadline (closed)
        self.closed_job = Job.objects.create(
            employer=self.employer,
            title="Closed Position",
            company_name="Old Corp",
            location="Boston",
            description="Test job description",
            job_type="Full-time",
            application_deadline=timezone.now().date() - timedelta(days=1),
            created_at=timezone.now() - timedelta(days=10)
        )

        # Create some candidates for testing applicant count
        Candidate.objects.create(
            job=self.open_job,
            user=self.employer_user,
            application_status='Pending'
        )

    def test_view_job_listings_authenticated(self):
        """Test viewing job listings when authenticated as admin"""
        response = self.client.get(reverse('admin_job_listings'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_job_listings.html')
        
        # Test context data
        self.assertEqual(response.context['total_jobs'], 3)
        self.assertEqual(response.context['open_jobs'], 2)  # Two open jobs
        self.assertEqual(response.context['closed_jobs'], 1)  # One closed job


    def test_search_functionality(self):
        """Test job listing search functionality"""
        # Test company name search
        response = self.client.get(reverse('admin_job_listings'), {'search': 'Tech Corp'})
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0].title, "Open Position")
        
        # Test title search
        response = self.client.get(reverse('admin_job_listings'), {'search': 'Closed'})
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0].title, "Closed Position")
        
        # Test location search
        response = self.client.get(reverse('admin_job_listings'), {'search': 'Remote'})
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0].title, "Open Position No Deadline")

    def test_status_filtering(self):
        """Test job status filtering"""
        # Test open jobs filter
        response = self.client.get(reverse('admin_job_listings'), {'status': 'open'})
        self.assertEqual(len(response.context['jobs']), 2)
        
        # Test closed jobs filter
        response = self.client.get(reverse('admin_job_listings'), {'status': 'closed'})
        self.assertEqual(len(response.context['jobs']), 1)
        
        # Test all jobs (no filter)
        response = self.client.get(reverse('admin_job_listings'), {'status': 'all'})
        self.assertEqual(len(response.context['jobs']), 3)

    def test_pagination(self):
        """Test pagination of job listings"""
        # Create more jobs to test pagination
        for i in range(7):  # Creates 7 more jobs (total 10 jobs)
            Job.objects.create(
                employer=self.employer,
                title=f"Pagination Test Job {i}",
                company_name="Test Company",
                location="Remote",
                created_at=timezone.now()
            )
        
        # Test first page
        response = self.client.get(reverse('admin_job_listings'))
        self.assertEqual(len(response.context['jobs']), 5)  # 5 jobs per page
        
        # Test second page
        response = self.client.get(reverse('admin_job_listings'), {'page': 2})
        self.assertEqual(len(response.context['jobs']), 5)
        
        # Test invalid page
        response = self.client.get(reverse('admin_job_listings'), {'page': 999})
        self.assertEqual(response.status_code, 200)  # Should still return last page
        
        # Test non-integer page
        response = self.client.get(reverse('admin_job_listings'), {'page': 'invalid'})
        self.assertEqual(response.status_code, 200)  # Should return first page

    def test_job_status_calculation(self):
        """Test correct calculation of job status"""
        response = self.client.get(reverse('admin_job_listings'))
        jobs = response.context['jobs']
        
        for job in jobs:
            if job.application_deadline is None:
                self.assertEqual(job.status, "Open")
            elif job.application_deadline < timezone.now().date():
                self.assertEqual(job.status, "Closed")
            else:
                self.assertEqual(job.status, "Open")

    def test_applicant_count(self):
        """Test correct calculation of applicant count for each job"""
        response = self.client.get(reverse('admin_job_listings'))
        jobs = response.context['jobs']
        
        for job in jobs:
            if job == self.open_job:
                self.assertEqual(job.applicant_count, 1)
            else:
                self.assertEqual(job.applicant_count, 0)


    def test_combined_filters(self):
        """Test combination of search and status filters"""
        # Test search with status filter
        response = self.client.get(
            reverse('admin_job_listings'),
            {'search': 'Tech', 'status': 'open'}
        )
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0].title, "Open Position")

    def test_ordering(self):
        """Test that jobs are ordered by creation date (newest first)"""
        response = self.client.get(reverse('admin_job_listings'))
        jobs = response.context['jobs']
        
        # Check that jobs are ordered by created_at in descending order
        self.assertTrue(all(
            jobs[i].created_at >= jobs[i+1].created_at 
            for i in range(len(jobs)-1)
        )) 

    @patch('tutorials.views.admin_views.logger')
    def test_edit_job(self, mock_logger):
        """Test editing job functionality"""
        # Initial job data
        job = Job.objects.create(
            employer=self.employer,
            title="Original Title",
            company_name="Original Company",
            location="Original Location",
            job_type="Part-time",
            salary=50000,
            description="Original description",
            requirements="Original requirements",
            benefits="Original benefits",
            application_deadline=timezone.now().date() + timedelta(days=30),
            contact_email="original@test.com"
        )

        # New job data
        updated_data = {
            'title': 'Updated Title',
            'company_name': 'Updated Company',
            'location': 'Updated Location',
            'job_type': 'Full-time',
            'salary': '60000.00',
            'description': 'Updated description',
            'requirements': 'Updated requirements',
            'benefits': 'Updated benefits',
            'application_deadline': (timezone.now().date() + timedelta(days=60)).strftime('%Y-%m-%d'),
            'contact_email': 'updated@test.com'
        }

        # Test GET request
        response = self.client.get(reverse('admin_edit_job', args=[job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_edit_job.html')
        self.assertEqual(response.context['job'], job)

        # Test POST request with updated data
        response = self.client.post(reverse('admin_edit_job', args=[job.id]), updated_data)
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertRedirects(response, reverse('admin_job_detail', args=[job.id]))

        # Verify job was updated
        job.refresh_from_db()
        self.assertEqual(job.title, updated_data['title'])
        self.assertEqual(job.company_name, updated_data['company_name'])
        self.assertEqual(job.location, updated_data['location'])
        self.assertEqual(job.job_type, updated_data['job_type'])
        self.assertEqual(float(job.salary), float(updated_data['salary']))
        self.assertEqual(job.description, updated_data['description'])
        self.assertEqual(job.requirements, updated_data['requirements'])
        self.assertEqual(job.benefits, updated_data['benefits'])
        self.assertEqual(job.contact_email, updated_data['contact_email'])

        # Test partial update (only some fields)
        partial_update = {
            'title': 'Partially Updated Title',
            'location': 'New Location'
        }
        response = self.client.post(reverse('admin_edit_job', args=[job.id]), partial_update)
        self.assertEqual(response.status_code, 302)

        # Verify partial update
        job.refresh_from_db()
        self.assertEqual(job.title, partial_update['title'])
        self.assertEqual(job.location, partial_update['location'])
        # Other fields should remain unchanged
        self.assertEqual(job.company_name, updated_data['company_name'])

        # Test invalid job ID
        response = self.client.get(reverse('admin_edit_job', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_admin_applications_view(self):
        """Test admin applications view functionality"""
        # Clear existing candidates
        Candidate.objects.all().delete()

        # Create test data
        candidate_statuses = ['Pending', 'Interview', 'Hired', 'Rejected']
        for status in candidate_statuses:
            for i in range(2):  # 2 candidates per status
                Candidate.objects.create(
                    job=self.open_job,
                    user=User.objects.create_user(
                        username=f'@candidate_{status}_{i}',
                        first_name=f'First{i}',
                        last_name=f'Last{i}',
                        email=f'candidate_{status}_{i}@test.com',
                        password='testpass123'
                    ),
                    application_status=status,
                    application_date=timezone.now() - timedelta(days=i)
                )

        # Test basic view
        response = self.client.get(reverse('admin_applications_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_applications_view.html')

        # Test statistics
        self.assertEqual(response.context['total_applications'], 8)
        self.assertEqual(response.context['pending_applications'], 2)
        self.assertEqual(response.context['interview_applications'], 2)
        self.assertEqual(response.context['hired_applications'], 2)
        self.assertEqual(response.context['rejected_applications'], 2)

        # Test search functionality
        response = self.client.get(reverse('admin_applications_view'), {'search': 'First0'})
        self.assertEqual(len(response.context['applications']), 4)  # One 'First0' per status

        # Test status filtering
        response = self.client.get(reverse('admin_applications_view'), {'status': 'Pending'})
        self.assertEqual(len(response.context['applications']), 2)

        # Test combined search and status filter
        response = self.client.get(reverse('admin_applications_view'), 
                                 {'search': 'First0', 'status': 'Hired'})
        self.assertEqual(len(response.context['applications']), 1)

        # Test pagination
        response = self.client.get(reverse('admin_applications_view'))
        self.assertEqual(len(response.context['applications']), 5)  # First page should have 5 items

        # Test second page
        response = self.client.get(reverse('admin_applications_view'), {'page': 2})
        self.assertEqual(len(response.context['applications']), 3)  # Second page should have remaining 3 items

        # Test invalid page number
        response = self.client.get(reverse('admin_applications_view'), {'page': 999})
        self.assertEqual(response.status_code, 200)  # Should return last page

        # Test non-integer page
        response = self.client.get(reverse('admin_applications_view'), {'page': 'invalid'})
        self.assertEqual(response.status_code, 200)  # Should return first page

        # Test ordering
        response = self.client.get(reverse('admin_applications_view'))
        applications = response.context['applications']
        self.assertTrue(all(
            applications[i].application_date >= applications[i+1].application_date
            for i in range(len(applications)-1)
        )) 

    @patch('tutorials.views.admin_views.logger')
    def test_toggle_job_status(self, mock_logger):
        """Test toggling job status between open and closed"""
        # Create a test job with future deadline (open)
        job = Job.objects.create(
            employer=self.employer,
            title="Test Toggle Job",
            company_name="Test Company",
            location="Test Location",
            application_deadline=timezone.now().date() + timedelta(days=30)
        )

        # Test closing the job
        close_data = {'status': 'Closed'}
        response = self.client.post(
            reverse('admin_toggle_job_status', args=[job.id]),
            data=json.dumps(close_data),
            content_type='application/json'
        )
        
        # Check response - Updated to expect {'status': 'success'}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'success'})
        
        # Verify job deadline was updated
        job.refresh_from_db()
        self.assertEqual(job.application_deadline, timezone.now().date())

        # Test reopening the job
        open_data = {'status': 'Open'}
        response = self.client.post(
            reverse('admin_toggle_job_status', args=[job.id]),
            data=json.dumps(open_data),
            content_type='application/json'
        )
        
        # Check response - Updated to expect {'status': 'success'}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'status': 'success'})
        
        # Verify job deadline was updated to 30 days from now
        job.refresh_from_db()
        self.assertEqual(job.application_deadline, timezone.now().date() + timedelta(days=30))

        # Test with invalid job ID
        response = self.client.post(
            reverse('admin_toggle_job_status', args=[999]),
            data=json.dumps(open_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

        # Test with invalid HTTP method (GET)
        response = self.client.get(reverse('admin_toggle_job_status', args=[job.id]))
        self.assertEqual(response.status_code, 405)  # Method not allowed

        # Test with invalid status
        invalid_data = {'status': 'Invalid'}
        response = self.client.post(
            reverse('admin_toggle_job_status', args=[job.id]),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        # Job deadline should remain unchanged
        job.refresh_from_db()
        self.assertEqual(job.application_deadline, timezone.now().date() + timedelta(days=30)) 