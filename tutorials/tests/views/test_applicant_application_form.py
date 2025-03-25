from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import Job, Employer
from django.contrib.messages import get_messages

User = get_user_model()

class ApplicantApplicationFormTests(TestCase):
    def setUp(self):
        # Create test user and applicant
        self.user = User.objects.create_user(
            username='testapplicant',
            password='testpass123',
            email='applicant@test.com',
            role='Applicant'
        )
        self.applicant = Applicant.objects.create(user=self.user)
        
        # Create test job
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
            status='approved'
        )
        
        self.client = Client()
        self.client.login(username='testapplicant', password='testpass123')
        
    def test_application_form_get(self):
        """Test getting the application form"""
        response = self.client.get(reverse('applicants_application', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_application.html')
        self.assertIn('form', response.context)
        
        
    def test_application_form_post_invalid(self):
        """Test submitting an invalid application form"""
        response = self.client.post(
            reverse('applicants_application', args=[self.job.id]),
            data={},  # Empty data to trigger form validation errors
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_application.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Please fix the errors in your application form.')
        
    def test_update_existing_application(self):
        """Test updating an existing application"""
        # Create initial application
        existing_application = Application.objects.create(
            applicant=self.applicant,
            job=self.job,
            cover_letter='Initial cover letter'
        )
        
        # Update the application
        form_data = {
            'cover_letter': 'Updated cover letter',
            'additional_info': 'Updated additional info'
        }
        
        response = self.client.post(
            reverse('applicants_application', args=[self.job.id]),
            data=form_data,
            follow=True
        )
        
        # Verify the update
        existing_application.refresh_from_db()
        self.assertEqual(existing_application.cover_letter, 'Updated cover letter')
        self.assertRedirects(response, reverse('job_detail', args=[self.job.id])) 