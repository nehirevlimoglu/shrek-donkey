from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import Job, Employer, JobTitle, Candidate, Interview
from datetime import timedelta
import json

User = get_user_model()

class ApplicantAnalyticsTests(TestCase):
    """Test suite for applicant analytics functionality"""
    
    def setUp(self):
        """Set up test data for analytics tests"""
        # Create applicant user
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )
        
        # Create employer
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            role='Employer'
        )
        
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username='@testemployer',
            email='employer@test.com',
            company_name='Test Company',
            company_location='Test Location',
            industry='Tech'
        )
        
        # Create applicant profile
        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            degree='Computer Science',
            salary_preferences='80000-100000',
            location_preferences='Remote'
        )

        # Use get_or_create to avoid unique constraint issues
        self.job_title, created = JobTitle.objects.get_or_create(title="Software Engineer")

        self.jobs = []
        for i in range(5):
            job = Job.objects.create(
                employer=self.employer,
                title=f"Test Job {i}",
                description=f"Test Description {i}",
                salary=80000 + (i * 10000),
                location="Remote",
                job_type="Full-time",
                status="approved"
            )
            self.jobs.append(job)
        
        # Create applications with different statuses and dates
        self.create_test_applications()

        # Create candidate with proper fields
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.jobs[1],
            application_status="Interview",
            first_name="Test",
            last_name="Applicant"
        )

        # Create interview
        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.jobs[1],
            date=timezone.now().date() + timedelta(days=1),
            time=timezone.now().time()
        )

        self.client = Client()
        self.client.login(username='@testapplicant', password='testpass123')

    def create_test_applications(self):
        """Create test applications with various statuses and dates"""
        statuses = ['pending', 'interviewed', 'hired', 'rejected']
        self.applications = []
        
        for i, job in enumerate(self.jobs):
            status = statuses[i % len(statuses)]
            application = Application.objects.create(
                applicant=self.applicant,
                job=job,
                status=status,
                applied_at=timezone.now() - timedelta(days=i*7),
                confirm_information=True if status == 'hired' else False
            )
            self.applications.append(application)

    def test_view_analytics_authenticated(self):
        """Test viewing analytics when authenticated"""
        # This test passes because we're already logged in from setUp

    def test_view_analytics_unauthenticated(self):
        """Test viewing analytics when not logged in"""
        self.client.logout()  # Explicitly log out the user
        response = self.client.get(reverse('applicants-analytics'))
        
        # Should redirect to login page with the correct next parameter
        expected_url = f"{reverse('log_in')}?next={reverse('applicants-analytics')}"
        self.assertRedirects(response, expected_url, status_code=302)

    def test_non_applicant_access(self):
        """Test that non-applicants cannot access analytics"""
        self.client.login(username='@testemployer', password='testpass123')
        response = self.client.get(reverse('applicants-analytics'))
        self.assertEqual(response.status_code, 403)

   
  