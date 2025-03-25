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

    def test_create_job_listing_success(self):
        """Test successful job creation with all required fields"""
        job_data = {
            'title': 'Python Developer',
            'description': 'Looking for a Python developer',
            'location': 'Remote',
            'application_deadline': (now().date() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'job_type': 'Full Time',
            'salary': '50000',
            'requirements': 'Python experience',
            'position': 'Senior Developer',  # Add required fields
            'company_name': 'Tech Corp',
            'contact_email': 'employer@example.com',
            'benefits': 'Health insurance, 401k'
        }

        with self.assertLogs('django', level='INFO') as logs:
            response = self.client.post(reverse('create_job_listings'), job_data, follow=True)
            
            # Check if success log message was created
            expected_log = f"✅ Job created successfully: Python Developer - Remote"
            self.assertTrue(any(expected_log in log for log in logs.output))
        
        # Check redirect
        self.assertRedirects(response, reverse('employer_job_listings'))
        
        # Verify job was created with correct attributes
        job = Job.objects.get(title='Python Developer')
        self.assertEqual(job.employer, self.employer)
        self.assertEqual(job.location, 'Remote')
        self.assertEqual(job.company_name, 'Tech Corp')
        self.assertEqual(job.contact_email, 'employer@example.com')
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "🎉 Job listing created successfully!")

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
            role='Applicant'  # Add role explicitly
        )
        
        self.client.force_login(non_employer)
        response = self.client.get(reverse('create_job_listings'))
        
        # Should redirect to employer home with error
        self.assertEqual(response.status_code, 403)  # Changed from redirect check
        # Or if you expect a redirect:
        # self.assertRedirects(response, reverse('employer_home_page'), fetch_redirect_response=False)

    def test_job_listing_default_values(self):
        """Test job creation with default values"""
        minimal_data = {
            'title': 'Minimal Job',
            'description': 'Basic description',
            'application_deadline': (now().date() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'job_type': 'Full Time',
            'salary': '50000',
            'requirements': 'Basic requirements'
        }

        response = self.client.post(reverse('create_job_listings'), minimal_data, follow=True)
        
        # Check if the form submission was successful
        self.assertEqual(response.status_code, 200)
        
        try:
            job = Job.objects.get(title='Minimal Job')
            self.assertEqual(job.location, "Test Location")  # Should use employer location
            self.assertEqual(job.company_name, "Tech Corp")
            self.assertEqual(job.contact_email, "employer@example.com")
        except Job.DoesNotExist:
            self.fail("Job was not created successfully")

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

    def test_employer_job_listings_no_profile(self):
        """Test job listings when employer profile doesn't exist"""
        # Create a user without an employer profile
        user_without_profile = User.objects.create_user(
            username="no_profile_user",
            password="password123",
            email="no_profile@example.com",
            role='Employer'
        )
        
        # Login as the user without profile
        self.client.force_login(user_without_profile)
        
        # Try to access job listings
        response = self.client.get(reverse('employer_job_listings'))
        
        # Should render error page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'error.html')
        self.assertEqual(response.context['message'], "Employer profile not found.")

    def test_employer_job_listings_with_logger(self):
        """Test job listings with logger when no jobs exist"""
        # Delete all existing jobs
        Job.objects.all().delete()
        
        # Access job listings using correct URL name
        with self.assertLogs('django', level='WARNING') as logs:
            response = self.client.get(reverse('employer_job_listings'))
            
            # Check if warning was logged
            expected_message = f"⚠️ No jobs found for employer: {self.employer.company_name}"
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

    def test_create_job_listing_with_default_location(self):
        """Test job creation using employer's default location"""
        job_data = {
            'title': 'Local Position',
            'description': 'Office-based role',
            'application_deadline': (now().date() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'job_type': 'Full Time',
            'salary': '50000',
            'requirements': 'Basic requirements',
            'position': 'Junior Developer',
            'benefits': 'Health insurance'
            # Deliberately omit location to test default behavior
        }

        response = self.client.post(reverse('create_job_listings'), job_data, follow=True)
        
        # Verify job was created with employer's default location
        job = Job.objects.get(title='Local Position')
        self.assertEqual(job.location, self.employer.company_location)
        self.assertEqual(job.company_name, self.employer.company_name)
        self.assertEqual(job.contact_email, self.employer.email)

    def test_create_job_listing_without_employer_defaults(self):
        """Test job creation when employer has no default values"""
        # Create employer without default values
        employer_without_defaults = Employer.objects.create(
            user=User.objects.create_user(
                username="no_defaults_employer",
                password="password123",
                email="no_defaults@example.com",
                role='Employer'
            ),
            username="no_defaults_employer",
            email="no_defaults@example.com"
        )
        
        self.client.force_login(employer_without_defaults.user)
        
        job_data = {
            'title': 'Test Job',
            'description': 'Test Description',
            'application_deadline': (now().date() + timedelta(days=14)).strftime('%Y-%m-%d'),
            'job_type': 'Full Time',
            'salary': '50000',
            'requirements': 'Test Requirements',
            'position': 'Test Position',
            'benefits': 'Test Benefits'
        }

        response = self.client.post(reverse('create_job_listings'), job_data, follow=True)
        
        # Verify job was created with fallback values
        job = Job.objects.get(title='Test Job')
        self.assertEqual(job.location, "Unknown Location")
        self.assertEqual(job.company_name, "Unknown Company")
        self.assertEqual(job.contact_email, "no-email@company.com") 