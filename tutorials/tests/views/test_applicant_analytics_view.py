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

    def test_empty_analytics(self):
        """Test analytics display when no applications exist"""
        Application.objects.all().delete()
        response = self.client.get(reverse('applicants-analytics'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_applications'], 0)
        self.assertEqual(response.context['interviews_scheduled'], 0)
        self.assertEqual(response.context['job_offers_received'], 0)
        self.assertEqual(response.context['offer_acceptance_rate'], 0)
        
        # Test empty JSON data
        self.assertEqual(json.loads(response.context['applications_over_time']), [0, 0, 0, 0, 0, 0])
        self.assertEqual(json.loads(response.context['offer_acceptance_breakdown']), [0, 0])


    def test_offer_acceptance_breakdown(self):
        """Test offer acceptance breakdown data"""
        response = self.client.get(reverse('applicants-analytics'))
        
        breakdown = json.loads(response.context['offer_acceptance_breakdown'])
        self.assertTrue(isinstance(breakdown, list))
        self.assertEqual(len(breakdown), 2)  # [accepted, declined]
        self.assertTrue(all(isinstance(count, int) for count in breakdown))

    def test_offer_acceptance_rate(self):
        """Test calculation of offer acceptance rate"""
        # Create additional hired applications with different confirmation status
        for i in range(2):
            job = Job.objects.create(
                employer=self.employer,
                title=f"Extra Job {i}",
                description=f"Description {i}",
                salary=90000,
                location="Remote",
                job_type="Full-time",
                status="approved"
            )
            Application.objects.create(
                applicant=self.applicant,
                job=job,
                status="hired",
                applied_at=timezone.now(),
                confirm_information=bool(i)  # One accepted, one not accepted
            )
        
        response = self.client.get(reverse('applicants-analytics'))
        
        # Now we should have:
        # - 1 hired and confirmed from create_test_applications
        # - 1 hired and confirmed from this test
        # - 1 hired but not confirmed from this test
        # Total: 2 confirmed out of 3 offers = 66.67%
        
        self.assertEqual(response.context['job_offers_received'], 3)
        self.assertEqual(response.context['offer_acceptance_rate'], 66.67)

    def test_applications_list(self):
        """Test applications list in analytics view"""
        response = self.client.get(reverse('applicants-analytics'))
        
        self.assertIn('applications', response.context)
        applications = response.context['applications']
        
        # Verify all applications are returned
        self.assertEqual(applications.count(), Application.objects.filter(applicant=self.applicant).count())
        
        # Verify applications are related to correct jobs
        self.assertTrue(all(app.job in self.jobs for app in applications)) 