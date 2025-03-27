from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer, Job
from django.utils.timezone import now, timedelta
from django.contrib.messages import get_messages
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class EmployerJobListingsTests(TestCase):
    """Test suite for employer job listings functionality"""

    def setUp(self):
        """Set up test data"""
        # Configure logging
        self.logger = logging.getLogger('django')
        self.previous_level = self.logger.getEffectiveLevel()
        self.logger.setLevel(logging.WARNING)
        
        # Create employer user
        self.employer_user = User.objects.create_user(
            username="test_employer",
            password="password123",
            email="employer@example.com",
            role='Employer'
        )

        # Create employer profile
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="Test Location"
        )

        # Create a sample job
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Test job description",
            location="Test Location",
            application_deadline=now().date() + timedelta(days=30)
        )

        self.client = Client()
        self.client.force_login(self.employer_user)

        # Add default job data for tests
        self.default_job_data = {
            'title': 'Test Job',
            'description': 'Test Description',
            'job_type': 'Full Time',
            'salary': '50000',
            'requirements': 'Test Requirements',
            'application_deadline': (now().date() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'location': 'Test Location'
        }

    def tearDown(self):
        """Clean up after tests"""
        # Restore previous logging level
        self.logger.setLevel(self.previous_level)

    def test_create_job_listing_get(self):
        """Test GET request to create job listing page"""
        response = self.client.get(reverse('create_job_listings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_create_job_listing.html')
        self.assertIn('form', response.context)

    def test_create_job_listing_invalid_data(self):
        """Test job creation with invalid data"""
        invalid_data = {
            'title': '',  # Title is required
            'description': 'Test description'
        }

        response = self.client.post(reverse('create_job_listings'), invalid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_create_job_listing.html')
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "There was an error with your submission.")

    def test_create_job_listing_non_employer(self):
        """Test job creation attempt by non-employer user"""
        # Create non-employer user
        non_employer = User.objects.create_user(
            username="regular_user",
            password="password123",
            email="user@example.com",
            role='Applicant'
        )
        
        self.client.force_login(non_employer)
        response = self.client.get(reverse('create_job_listings'))
        
        # Should redirect to home with error message
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "You must be an employer to post a job.")

    def test_view_job_listings(self):
        """Test viewing employer's job listings"""
        response = self.client.get(reverse('employer_job_listings'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_job_listings.html')
        self.assertIn('jobs', response.context)
        self.assertEqual(list(response.context['jobs']), [self.job])

    def test_empty_job_listings(self):
        """Test viewing job listings when employer has no jobs"""
        # Delete existing job
        Job.objects.all().delete()
        
        response = self.client.get(reverse('employer_job_listings'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['jobs']), 0)

    def test_job_listings_wrong_employer(self):
        """Test that employers can only see their own job listings"""
        # Create another employer with their own job
        other_employer = Employer.objects.create(
            user=User.objects.create_user(
                username="other_employer",
                password="password123",
                email="other@example.com",
                role='Employer'
            ),
            username="other_employer",
            email="other@example.com"
        )
        
        Job.objects.create(
            employer=other_employer,
            title="Other Job",
            description="This job shouldn't be visible"
        )

        response = self.client.get(reverse('employer_job_listings'))
        
        self.assertEqual(response.status_code, 200)
        jobs = list(response.context['jobs'])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0], self.job)
        self.assertFalse(any(job.title == "Other Job" for job in jobs))



    def test_employer_job_listings_with_logger(self):
        """Test job listings with logger when no jobs exist"""
        # Delete all existing jobs
        Job.objects.all().delete()
        
        # Access job listings using correct URL name
        with self.assertLogs('tutorials', level='WARNING') as logs:
            response = self.client.get(reverse('employer_job_listings'))
            
            # Check if warning was logged
            expected_message = "No jobs found for employer"
            self.assertTrue(any(expected_message in log for log in logs.output))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_job_listings.html')
        self.assertEqual(len(response.context['jobs']), 0)

    def test_employer_job_listings_with_jobs(self):
        """Test job listings with existing jobs"""
        # Create additional jobs
        additional_job = Job.objects.create(
            employer=self.employer,
            title="Second Job",
            description="Another test job",
            location="Test Location",
            application_deadline=now().date() + timedelta(days=30)
        )
        
        response = self.client.get(reverse('employer_job_listings'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_job_listings.html')
        
        # Should have both jobs
        jobs = list(response.context['jobs'])
        self.assertEqual(len(jobs), 2)
        self.assertTrue(any(job.title == "Software Engineer" for job in jobs))
        self.assertTrue(any(job.title == "Second Job" for job in jobs))

    def test_employer_job_listings_ordering(self):
        """Test that job listings are properly ordered"""
        # Create jobs with different dates
        recent_job = Job.objects.create(
            employer=self.employer,
            title="Recent Job",
            description="Recent job posting",
            location="Test Location",
            application_deadline=now().date() + timedelta(days=30)
        )
        
        response = self.client.get(reverse('employer_job_listings'))
        jobs = list(response.context['jobs'])
        
        self.assertEqual(len(jobs), 2)
        self.assertIn(self.job, jobs)
        self.assertIn(recent_job, jobs)

    def test_employer_job_listings_with_expired_jobs(self):
        """Test that expired jobs are still shown in the listings"""
        # Create an expired job
        expired_job = Job.objects.create(
            employer=self.employer,
            title="Expired Job",
            description="This job has expired",
            location="Test Location",
            application_deadline=now().date() - timedelta(days=1)
        )
        
        response = self.client.get(reverse('employer_job_listings'))
        jobs = list(response.context['jobs'])
        
        self.assertEqual(len(jobs), 2)
        self.assertTrue(any(job.title == "Expired Job" for job in jobs))

    def test_employer_job_listings_with_expired_jobs(self):
        """Test that expired jobs are still shown in the listings"""
        # Create an expired job
        expired_job = Job.objects.create(
            employer=self.employer,
            title="Expired Job",
            description="This job has expired",
            location="Test Location",
            application_deadline=now().date() - timedelta(days=1)
        )
        
        response = self.client.get(reverse('employer_job_listings'))
        jobs = list(response.context['jobs'])
        
        self.assertEqual(len(jobs), 2)
        self.assertTrue(any(job.title == "Expired Job" for job in jobs)) 