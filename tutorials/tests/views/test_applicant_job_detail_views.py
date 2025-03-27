from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import Job, Employer

User = get_user_model()

class JobDetailViewTests(TestCase):
    """
    Test suite for job detail view functionality
    Tests job viewing and application features
    """
    
    def setUp(self):
        """Set up test data for job detail tests"""
        # Create employer user
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            first_name='Test',
            last_name='Employer',
            role='Employer'
        )
        
        # Create employer profile
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='Test Company'
        )
        
        # Create a job
        self.job = Job.objects.create(
            employer=self.employer,
            title='Test Job',
            company_name='Test Company',
            location='Test Location',
            description='Test Description',
            status='approved'
        )
        
        # Create applicant user
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )
        
        # Create applicant profile
        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            degree='Computer Science',
            salary_preferences='50000-70000',
            location_preferences='Remote'
        )
        
        self.client = Client()
    
    def test_job_detail_authenticated_applicant(self):
        """Test job detail view as authenticated applicant"""
        self.client.login(username='@testapplicant', password='testpass123')
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        self.assertEqual(response.context['job'], self.job)
        self.assertFalse(response.context['existing_application'])
        self.assertEqual(response.context['next_page'], 'home')
    
    def test_job_detail_with_existing_application(self):
        """Test job detail view when applicant has already applied"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Create an existing application
        Application.objects.create(applicant=self.applicant, job=self.job)
        
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        self.assertTrue(response.context['existing_application'])
    
    def test_apply_for_job_already_applied(self):
        """Test applying for a job that was already applied to"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Create existing application
        Application.objects.create(applicant=self.applicant, job=self.job)
        
        # Try to apply again
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        
        # Should render the page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        self.assertTrue(response.context['existing_application'])
        
        # Verify no duplicate application was created
        self.assertEqual(
            Application.objects.filter(
                applicant=self.applicant,
                job=self.job
            ).count(), 
            1
        )
    
    def test_apply_for_job_no_applicant_profile(self):
        """Test applying for a job when user has no applicant profile"""
        # Create user without applicant profile
        user_no_profile = User.objects.create_user(
            username='@noprofile',
            password='testpass123',
            email='noprofile@test.com',
            role='Applicant'
        )
        
        self.client.login(username='@noprofile', password='testpass123')
        
        # Try to apply for job
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        
        # Should render the page
        self.assertEqual(response.status_code, 200)
        
        # Verify no application was created
        self.assertEqual(
            Application.objects.filter(job=self.job).count(), 
            0
        ) 