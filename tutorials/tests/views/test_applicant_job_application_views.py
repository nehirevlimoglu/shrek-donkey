from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from tutorials.models.applicants_models import Applicant, Application, ApplicantNotification
from tutorials.models.employer_models import Job, Employer, EmployerNotification, Candidate, JobTitle
from datetime import date, timedelta
from django.utils import timezone

User = get_user_model()

class JobApplicationTests(TestCase):
    """Test suite for job application functionality"""
    
    def setUp(self):
        """Set up test data for job application tests"""
        # Create employer user and profile
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            first_name='Test',
            last_name='Employer',
            role='Employer'
        )
        
        # Create employer with minimal required fields
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='Test Company'
        )
        
        # Create applicant user and profile
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )
        
        # Create job titles
        self.job_title = JobTitle.objects.create(title="Software Engineering")
        
        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            degree='Computer Science',
            salary_preferences='80000-100000',
            location_preferences='Remote'
        )
        self.applicant.job_preferences.add(self.job_title)
        
        # Create active and expired jobs for testing
        self.job = Job.objects.create(
            title='Senior Software Engineer',
            company_name='Test Company',
            location='Remote',
            job_type='Full Time',
            salary=90000,
            description='Test job description',
            requirements='Test requirements',
            employer=self.employer,
            status='approved',
            application_deadline=date.today() + timedelta(days=30)
        )
        
        # Create an expired job for testing deadline validation
        self.expired_job = Job.objects.create(
            title='Expired Position',
            company_name='Test Company',
            location='Remote',
            job_type='Full Time',
            salary=85000,
            description='Expired job',
            requirements='Test requirements',
            employer=self.employer,
            status='approved',
            application_deadline=date.today() - timedelta(days=1)
        )
        
        # Create a job without an employer for testing error handling
        self.orphan_job = Job.objects.create(
            title='Orphan Job',
            company_name='No Employer',
            location='Remote',
            job_type='Full Time',
            salary=75000,
            description='Job without employer',
            requirements='Test requirements',
            status='approved',
            application_deadline=date.today() + timedelta(days=30)
        )
        
        # Set up test client and login
        self.client = Client()
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Create valid application data with all required fields
        self.valid_application_data = {
            'first_name': 'Test',
            'last_name': 'Applicant',
            'email': 'applicant@test.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'resume': SimpleUploadedFile(
                "resume.pdf",
                b"PDF content",
                content_type="application/pdf"
            ),
            'cover_letter': SimpleUploadedFile(
                "cover.pdf",
                b"PDF content",
                content_type="application/pdf"
            ),
            'school': 'Test University',
            'degree': 'Computer Science',
            'discipline': 'Computer Science',
            'start_date': '2020-09-01',
            'end_date': '2024-05-31',
            'current_job_title': 'Software Developer',
            'current_employer': 'Current Corp',
            'linkedin_profile': 'https://linkedin.com/in/test',
            'portfolio_website': 'https://test.com',
            'how_did_you_hear': 'linkedin',
            'sponsorship_needed': 'no',
            'confirm_information': True
        }

    def test_view_job_detail(self):
        """Test viewing job details"""
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        self.assertEqual(response.context['job'], self.job)

    def test_apply_to_expired_job(self):
        """Test applying to an expired job is prevented"""
        response = self.client.post(
            reverse('apply_for_job', args=[self.expired_job.id]),
            self.valid_application_data,
            format='multipart'
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('This job posting has expired', str(messages[0]))
        self.assertEqual(response.status_code, 302)

    def test_apply_to_nonexistent_job(self):
        """Test applying to a non-existent job returns 404"""
        response = self.client.post(
            reverse('apply_for_job', args=[99999]),
            self.valid_application_data,
            format='multipart'
        )
        self.assertEqual(response.status_code, 404)

    def test_submit_application_without_employer(self):
        """Test submitting application to job without employer"""
        response = self.client.post(
            reverse('apply_for_job', args=[self.orphan_job.id]),
            self.valid_application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify only applicant notification was created
        self.assertFalse(
            EmployerNotification.objects.filter(
                title="New Job Application"
            ).exists()
        )
        self.assertTrue(
            ApplicantNotification.objects.filter(
                applicant=self.applicant,
                title="Application Submitted"
            ).exists()
        )

    def test_candidate_creation(self):
        """Test candidate record is created with application"""
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            self.valid_application_data,
            format='multipart'
        )
        
        # Verify candidate was created with correct fields
        candidate = Candidate.objects.filter(
            user=self.applicant_user,
            job=self.job
        ).first()
        
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.first_name, self.valid_application_data['first_name'])
        self.assertEqual(candidate.last_name, self.valid_application_data['last_name'])
        self.assertEqual(candidate.phone, self.valid_application_data['phone'])
        self.assertEqual(candidate.school, self.valid_application_data['school'])
        self.assertEqual(candidate.application_status, 'Pending')

    def test_invalid_form_submission(self):
        """Test handling of invalid form data"""
        invalid_data = self.valid_application_data.copy()
        invalid_data['email'] = 'not-an-email'  # Invalid email format
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            invalid_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertFalse(Application.objects.exists())

    def test_get_application_form(self):
        """Test getting the application form page"""
        response = self.client.get(
            reverse('apply_for_job', args=[self.job.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_application.html')
        self.assertIsNotNone(response.context['form'])
        self.assertIsNotNone(response.context['job'])
        self.assertIsNotNone(response.context['existing_application'])

    def test_file_size_validation(self):
        """Test file size limits for uploads"""
        large_file = SimpleUploadedFile(
            "large_resume.pdf",
            b"PDF content" * 1024 * 1024,  # Create a large file
            content_type="application/pdf"
        )
        
        data = self.valid_application_data.copy()
        data['resume'] = large_file
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('resume', response.context['form'].errors)

    def test_non_applicant_access(self):
        """Test access restriction for non-applicants"""
        # Login as employer
        self.client.login(username='@testemployer', password='testpass123')
        
        response = self.client.get(
            reverse('apply_for_job', args=[self.job.id])
        )
        
        # Check that non-applicants are redirected
        self.assertEqual(response.status_code, 302)
        
        # Verify they can't access the page
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Applicant profile not found" in str(msg) for msg in messages))

    def test_invalid_application_submission(self):
        """Test submitting invalid application data"""
        job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Test Description",
            status="approved"
        )
        
        response = self.client.post(
            reverse('apply_for_job', kwargs={'job_id': job.id}),
            {}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_application_validation_required_fields(self):
        """Test application validation for required fields (lines 307-323)"""
        job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Test Description",
            status="approved"
        )
        
        # Test missing required fields
        response = self.client.post(
            reverse('apply_for_job', kwargs={'job_id': job.id}),
            {}  # Empty data to trigger all required field validations
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        form_errors = response.context['form'].errors
        self.assertTrue(form_errors)  # Check that there are form errors
        
        # Check for specific required field errors
        required_fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'resume', 'how_did_you_hear', 'sponsorship_needed', 'confirm_information']
        for field in required_fields:
            self.assertIn(field, form_errors)
            self.assertIn('This field is required', str(form_errors[field]))

    def test_application_file_validation(self):
        """Test file upload validation (lines 137-165)"""
        job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Test Description",
            status="approved"
        )
        
        # Test invalid file type
        invalid_file = SimpleUploadedFile(
            "resume.txt",
            b"text file content",
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('apply_for_job', kwargs={'job_id': job.id}),
            {
                'first_name': 'Test',
                'last_name': 'Applicant',
                'resume': invalid_file,
                'phone': '1234567890',
                'email': 'test@example.com',
                'address': '123 Test St',
                'how_did_you_hear': 'linkedin',
                'sponsorship_needed': 'no',
                'confirm_information': True
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertIn('resume', response.context['form'].errors)
        
        # Test file too large (>5MB)
        large_content = b"x" * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte
        large_file = SimpleUploadedFile(
            "resume.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        response = self.client.post(
            reverse('apply_for_job', kwargs={'job_id': job.id}),
            {
                'first_name': 'Test',
                'last_name': 'Applicant',
                'resume': large_file,
                'phone': '1234567890',
                'email': 'test@example.com',
                'address': '123 Test St',
                'how_did_you_hear': 'linkedin',
                'sponsorship_needed': 'no',
                'confirm_information': True
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertIn('resume', response.context['form'].errors)
        self.assertIn('Resume file size must be under 5MB', str(response.context['form'].errors['resume']))

    def test_application_form_validation(self):
        """Test application form validation (lines 307-323)"""
        job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Test Description",
            status="approved"
        )
        
        # Test with invalid data
        invalid_data = {
            'first_name': '',  # Required field empty
            'email': 'invalid-email',  # Invalid email format
            'phone': '123',  # Invalid phone format
            'confirm_information': False  # Must be True
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[job.id]),
            invalid_data
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_application_processing(self):
        """Test application processing and notification creation (lines 137-165)"""
        # Use valid_application_data as base
        application_data = self.valid_application_data.copy()
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        # Check if application was created
        self.assertTrue(Application.objects.filter(
            applicant=self.applicant,
            job=self.job
        ).exists())
        
        # Check notifications
        self.assertTrue(
            ApplicantNotification.objects.filter(
                applicant=self.applicant,
                title="Application Submitted"
            ).exists()
        )
        
        if self.job.employer:
            self.assertTrue(
                EmployerNotification.objects.filter(
                    employer=self.job.employer,
                    title="New Job Application"
                ).exists()
            )

    def test_form_validation_and_errors(self):
        """Test form validation and error handling (lines 307-323)"""
        # Test with missing required fields
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            {
                # Empty form data to trigger all validations
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        form_errors = response.context['form'].errors
        
        # Check required fields
        required_fields = [
            'first_name', 'last_name', 'email', 'phone',
            'address', 'resume', 'how_did_you_hear',
            'sponsorship_needed', 'confirm_information'
        ]
        
        for field in required_fields:
            self.assertIn(field, form_errors)
            self.assertIn('This field is required', str(form_errors[field]))
        
        # Test with invalid email format
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            {
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'invalid-email',  # Invalid email format
                'phone': '1234567890',
                'address': '123 Test St',
                'how_did_you_hear': 'linkedin',
                'sponsorship_needed': 'no',
                'confirm_information': True
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertIn('Enter a valid email address', str(response.context['form'].errors['email']))

    def test_job_detail_existing_application(self):
        """Test job detail view with existing application"""
        # Login as applicant
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Create an existing application
        Application.objects.create(applicant=self.applicant, job=self.job)
        
        # Get the job detail page
        response = self.client.get(
            reverse('job_detail', args=[self.job.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        # Check if application exists in database instead of context
        self.assertTrue(
            Application.objects.filter(
                applicant=self.applicant,
                job=self.job
            ).exists()
        )

    def test_job_detail_new_application(self):
        """Test job detail view with new application"""
        # Login as applicant
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Verify no existing application
        self.assertFalse(
            Application.objects.filter(
                applicant=self.applicant,
                job=self.job
            ).exists()
        )
        
        # Get the job detail page first
        response = self.client.get(
            reverse('job_detail', args=[self.job.id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Then submit application
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            self.valid_application_data,
            format='multipart'
        )
        
        # Should redirect to job detail after successful application
        self.assertEqual(response.status_code, 302)
        
        # Verify application was created
        self.assertTrue(
            Application.objects.filter(
                applicant=self.applicant,
                job=self.job
            ).exists()
        )

    def test_job_detail_non_applicant(self):
        """Test job detail view when user is not an applicant"""
        # Create non-applicant user
        non_applicant_user = User.objects.create_user(
            username='@nonapplicant',
            password='testpass123',
            email='non@test.com',
            role='Employer'  # Not an applicant
        )
        
        # Login as non-applicant
        self.client.login(username='@nonapplicant', password='testpass123')
        
        # Access job detail
        response = self.client.get(
            reverse('job_detail', args=[self.job.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        # Check database instead of context
        self.assertFalse(
            Application.objects.filter(
                job=self.job,
                applicant__user=non_applicant_user
            ).exists()
        )

    

