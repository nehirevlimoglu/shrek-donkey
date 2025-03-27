from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import Job, Employer
from django.contrib.messages import get_messages
from random import randint
from datetime import date, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class ApplicantJobDetailTests(TestCase):
    def setUp(self):
        # Create test user and applicant
        self.user = User.objects.create_user(
            username='testapplicant',
            password='testpass123',
            email='applicant@test.com',
            role='Applicant'
        )
        self.applicant = Applicant.objects.create(user=self.user)
        
        # Create test employer and job
        self.employer = Employer.objects.create(
            user=User.objects.create_user(
                username='testemployer',
                password='testpass123',
                email='employer@test.com',
                role='Employer'
            ),
            company_name='Test Company'
        )
        
        self.job = Job.objects.create(
            employer=self.employer,
            title='Test Job',
            company_name='Test Company',
            location='Test Location',
            description='Test Description',
            status='approved',
            application_deadline=date.today() + timedelta(days=30)
        )
        
        self.client = Client()
        
    def test_job_detail_view_unauthenticated(self):
        """Test job detail view for unauthenticated user"""
        # Expect redirect to login page for unauthenticated users
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 302)  # Changed from 200 to 302
        self.assertRedirects(response, f'/log_in/?next=/job/{self.job.id}/')
        
    def test_job_detail_view_authenticated(self):
        """Test job detail view for authenticated applicant"""
        self.client.login(username='testapplicant', password='testpass123')
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        self.assertFalse(response.context['existing_application'])
        
        
    def test_job_detail_post_new_application(self):
        """Test submitting a new application via POST"""
        self.client.login(username='testapplicant', password='testpass123')
        
        # Create application data with required fields
        application_data = {
            'first_name': 'Test',
            'last_name': 'Applicant',
            'email': 'applicant@test.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'resume': SimpleUploadedFile(
                "resume.pdf",
                b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
                content_type="application/pdf"
            ),
            'how_did_you_hear': 'linkedin',
            'sponsorship_needed': 'no',
            'confirm_information': True,
            'skills': 'Python, Django, Testing'
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/job/{self.job.id}/?applied=true")
        
        # Verify application was created
        self.assertTrue(
            Application.objects.filter(
                applicant=self.applicant,
                job=self.job
            ).exists()
        )
        
    def test_job_detail_post_duplicate_application(self):
        """Test submitting a duplicate application"""
        self.client.login(username='testapplicant', password='testpass123')
        # Create existing application
        Application.objects.create(applicant=self.applicant, job=self.job)
        
        response = self.client.post(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['existing_application'])

    def test_job_detail_non_applicant_user(self):
        """Test job detail view for authenticated user who is not an applicant"""
        # Create a non-applicant user
        non_applicant = User.objects.create_user(
            username='nonapplicant',
            password='testpass123',
            email='non@test.com',
            role='Employer'  # Not an applicant role
        )
        self.client.login(username='nonapplicant', password='testpass123')
        
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['existing_application'])

    def test_job_detail_post_without_applicant_profile(self):
        """Test POST request when user has no applicant profile"""
        # Create user without applicant profile
        user_no_profile = User.objects.create_user(
            username='noprofile',
            password='testpass123',
            email='noprofile@test.com',
            role='Applicant'
        )
        self.client.login(username='noprofile', password='testpass123')
        
        response = self.client.post(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)  # Stays on same page
        self.assertFalse(Application.objects.filter(job=self.job).exists())

   

    def test_job_detail_post_duplicate_application(self):
        """Test attempting to submit duplicate application"""
        self.client.login(username='testapplicant', password='testpass123')
        
        # Create initial application
        Application.objects.create(applicant=self.applicant, job=self.job)
        
        # Attempt to apply again
        response = self.client.post(reverse('job_detail', args=[self.job.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['existing_application'])
        # Verify only one application exists
        self.assertEqual(
            Application.objects.filter(applicant=self.applicant, job=self.job).count(),
            1
        )

    def test_job_detail_invalid_job_id(self):
        """Test accessing job detail with invalid job ID"""
        self.client.login(username='testapplicant', password='testpass123')
        
        response = self.client.get(reverse('job_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_job_detail_post_success_redirect(self):
        """Test successful application submission redirect"""
        self.client.login(username='testapplicant', password='testpass123')
        
        # Create application data with required fields
        application_data = {
            'first_name': 'Test',
            'last_name': 'Applicant',
            'email': 'applicant@test.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'resume': SimpleUploadedFile(
                "resume.pdf",
                b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
                content_type="application/pdf"
            ),
            'how_did_you_hear': 'linkedin',
            'sponsorship_needed': 'no',
            'confirm_information': True,
            'skills': 'Python, Django, Testing'
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/job/{self.job.id}/?applied=true")
        
        # Verify application was created
        self.assertTrue(
            Application.objects.filter(
                applicant=self.applicant,
                job=self.job
            ).exists()
        ) 