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
        
        # Create PDF test files
        self.pdf_content = b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj"
        self.valid_resume = SimpleUploadedFile(
            "resume.pdf",
            self.pdf_content,
            content_type="application/pdf"
        )
        self.valid_cover_letter = SimpleUploadedFile(
            "cover.pdf",
            self.pdf_content,
            content_type="application/pdf"
        )
        
        # Create valid application data
        self.valid_application_data = {
            'first_name': 'Test',
            'last_name': 'Applicant',
            'email': 'applicant@test.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'resume': self.valid_resume,
            'cover_letter': self.valid_cover_letter,
            'school': 'Test University',
            'degree': 'Computer Science',
            'discipline': 'bachelors',  # Changed to match form choices
            'start_date_month': '1',
            'start_date_day': '1',
            'start_date_year': '2020',
            'end_date_month': '1',
            'end_date_day': '1',
            'end_date_year': '2024',
            'current_job_title': 'Software Developer',
            'current_employer': 'Current Corp',
            'linkedin_profile': 'https://linkedin.com/in/test',
            'portfolio_website': 'https://test.com',
            'how_did_you_hear': 'linkedin',
            'sponsorship_needed': 'no',
            'confirm_information': True,
            'skills': 'Python, Django, Testing'
        }

    def test_view_job_detail(self):
        """Test viewing job details"""
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        self.assertEqual(response.context['job'], self.job)

    def test_apply_to_expired_job(self):
        """Test applying to an expired job is prevented"""
        # Create an expired job with a deadline in the past
        expired_job = Job.objects.create(
            title='Expired Position',
            company_name='Test Company',
            location='Remote',
            job_type='Full Time',
            salary=85000,
            description='Expired job',
            requirements='Test requirements',
            employer=self.employer,
            status='approved',
            application_deadline=date.today() - timedelta(days=1)  # Set deadline to yesterday
        )
        
        response = self.client.post(
            reverse('apply_for_job', args=[expired_job.id]),
            self.valid_application_data,
            format='multipart'
        )
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('job_detail', args=[expired_job.id]))
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "This job posting has expired")
        
        # Verify no application was created
        self.assertFalse(
            Application.objects.filter(
                job=expired_job,
                applicant=self.applicant
            ).exists()
        )

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

    def test_submit_valid_application(self):
        """Test submitting a valid application"""
        self.client.login(username='@testapplicant', password='testpass123')
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            self.valid_application_data,
            format='multipart'
        )
        
        # Should redirect after successful submission
        self.assertRedirects(response, f"/job/{self.job.id}/?applied=true")
        
        # Verify application was created
        application = Application.objects.filter(
            applicant=self.applicant,
            job=self.job
        ).first()
        self.assertIsNotNone(application)
        
        # Verify notifications were created
        self.assertTrue(
            ApplicantNotification.objects.filter(
                applicant=self.applicant,
                title="Application Submitted"
            ).exists()
        )
        self.assertTrue(
            EmployerNotification.objects.filter(
                employer=self.job.employer,
                title="New Job Application"
            ).exists()
        )

    def test_invalid_form_submission(self):
        """Test handling of invalid form data"""
        self.client.login(username='@testapplicant', password='testpass123')
        invalid_data = self.valid_application_data.copy()
        invalid_data['email'] = 'not-an-email'
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            invalid_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertFalse(Application.objects.exists())

    def test_file_validation(self):
        """Test file upload validation"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Test invalid file type
        invalid_data = self.valid_application_data.copy()
        invalid_data['resume'] = SimpleUploadedFile(
            "resume.txt",
            b"text content",
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            invalid_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('resume', response.context['form'].errors)
        self.assertIn('Only PDF files are allowed', str(response.context['form'].errors['resume']))

    def test_duplicate_application(self):
        """Test preventing duplicate applications"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Submit first application
        first_response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            self.valid_application_data,
            format='multipart'
        )
        
        # Verify first application was successful
        self.assertEqual(first_response.status_code, 302)
        self.assertRedirects(first_response, f"/job/{self.job.id}/?applied=true")
        
        # Create new file objects for second submission (since files can't be reused)
        second_data = self.valid_application_data.copy()
        second_data['resume'] = SimpleUploadedFile(
            "resume.pdf",
            self.pdf_content,
            content_type="application/pdf"
        )
        second_data['cover_letter'] = SimpleUploadedFile(
            "cover.pdf",
            self.pdf_content,
            content_type="application/pdf"
        )
        
        # Try to submit duplicate application
        second_response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            second_data,
            format='multipart'
        )
        
        # Should redirect back to job detail
        self.assertRedirects(second_response, reverse('job_detail', args=[self.job.id]))
        
        # Check error message
        messages = list(get_messages(second_response.wsgi_request))
        self.assertTrue(any(
            "You have already applied for this job" in str(message)
            for message in messages
        ))
        
        # Verify only one application exists
        self.assertEqual(
            Application.objects.filter(
                applicant=self.applicant,
                job=self.job
            ).count(),
            1
        )

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
        
        # Try to access the application form
        response = self.client.get(
            reverse('apply_for_job', args=[self.job.id])
        )
        
        # Check that non-applicants get a 404 response
        self.assertEqual(response.status_code, 404)
        
        # Try to submit an application
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            self.valid_application_data,
            format='multipart'
        )
        
        # Check that submission also returns 404
        self.assertEqual(response.status_code, 404)
        
        # Verify no application was created
        self.assertFalse(
            Application.objects.filter(
                job=self.job,
                applicant__user=self.employer_user
            ).exists()
        )

    def test_invalid_application_submission(self):
        """Test submitting invalid application data"""
        job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Test Description",
            status="approved",
            application_deadline=date.today() + timedelta(days=30)
        )
        
        response = self.client.post(
            reverse('apply_for_job', kwargs={'job_id': job.id}),
            {}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_application_validation_required_fields(self):
        """Test application validation for required fields"""
        job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Test Description",
            status="approved",
            application_deadline=date.today() + timedelta(days=30)
        )
        
        # Test missing required fields
        response = self.client.post(
            reverse('apply_for_job', kwargs={'job_id': job.id}),
            {}  # Empty data to trigger all required field validations
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        form_errors = response.context['form'].errors
        self.assertTrue(form_errors)
        
        # Check for specific required field errors
        required_fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'resume', 'how_did_you_hear', 'sponsorship_needed', 'confirm_information']
        for field in required_fields:
            self.assertIn(field, form_errors)
            self.assertIn('This field is required', str(form_errors[field]))

    def test_application_file_validation(self):
        """Test file upload validation"""
        job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Test Description",
            status="approved",
            application_deadline=date.today() + timedelta(days=30)
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

    def test_application_form_validation(self):
        """Test application form validation"""
        job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Test Description",
            status="approved",
            application_deadline=date.today() + timedelta(days=30)
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
        """Test application processing and notification creation"""
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
        """Test form validation and error handling"""
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

    def test_application_deadline_validation(self):
        """Test that applications are rejected for jobs past their deadline"""
        # Create a job with deadline in the past
        past_deadline_job = Job.objects.create(
            employer=self.employer,
            title="Past Deadline Job",
            description="Test Description",
            status="approved",
            application_deadline=date.today() - timedelta(days=1)  # Yesterday
        )
        
        response = self.client.post(
            reverse('apply_for_job', args=[past_deadline_job.id]),
            self.valid_application_data,
            format='multipart'
        )
        
        # Should redirect to job detail
        self.assertRedirects(response, reverse('job_detail', args=[past_deadline_job.id]))
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "This job posting has expired")
        
        # Verify no application was created
        self.assertFalse(
            Application.objects.filter(
                job=past_deadline_job,
                applicant=self.applicant
            ).exists()
        )

    def test_work_experience_creation(self):
        """Test creation of work experience entries during application submission"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            'skills': 'Python, Django, Testing',
            # Add work experience data
            'work_job_title[]': ['Software Engineer', 'Developer'],
            'work_employer[]': ['Company A', 'Company B'],
            'work_start_date[]': ['2020-01-01', '2018-01-01'],
            'work_end_date[]': ['2022-01-01', '2019-12-31'],
            'job_description[]': ['Description 1', 'Description 2']
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify work experiences were created
        candidate = Candidate.objects.get(user=self.applicant_user, job=self.job)
        work_experiences = candidate.work_experiences.all()
        
        self.assertEqual(work_experiences.count(), 2)
        self.assertEqual(work_experiences[0].job_title, 'Software Engineer')
        self.assertEqual(work_experiences[1].job_title, 'Developer')

    def test_education_and_work_experience_parsing(self):
        """Test parsing of education and work experience data during application submission"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            'skills': 'Python, Django, Testing',
            # Add education data
            'school[]': ['University A', 'College B'],
            'degree[]': ['Bachelor', 'Master'],
            'discipline[]': ['Computer Science', 'Software Engineering'],
            'start_date[]': ['2016-09-01', '2020-09-01'],
            'end_date[]': ['2020-05-31', '2022-05-31'],
            # Add work experience data
            'work_job_title[]': ['Software Engineer', 'Developer'],
            'work_employer[]': ['Company A', 'Company B'],
            'work_start_date[]': ['2020-01-01', '2018-01-01'],
            'work_end_date[]': ['2022-01-01', '2019-12-31'],
            'job_description[]': ['Description 1', 'Description 2']
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify application was created with education and work experience data
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        
        # Check education data
        self.assertEqual(len(application.education), 2)
        self.assertEqual(application.education[0]['school'], 'University A')
        self.assertEqual(application.education[1]['school'], 'College B')
        
        # Check work experience data
        self.assertEqual(len(application.work_experience), 2)
        self.assertEqual(application.work_experience[0]['work_job_title'], 'Software Engineer')
        self.assertEqual(application.work_experience[1]['work_job_title'], 'Developer')
        
        # Verify candidate was created with work experiences
        candidate = Candidate.objects.get(user=self.applicant_user, job=self.job)
        work_experiences = candidate.work_experiences.all()
        self.assertEqual(work_experiences.count(), 2)

    def test_education_data_parsing(self):
        """Test parsing and saving of education data during application submission"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            'skills': 'Python, Django, Testing',
            # Add multiple education entries
            'school[]': ['MIT', 'Stanford', 'Harvard'],
            'degree[]': ['BSc', 'MSc', 'PhD'],
            'discipline[]': ['Computer Science', 'Software Engineering', 'AI'],
            'start_date[]': ['2015-09-01', '2019-09-01', '2021-09-01'],
            'end_date[]': ['2019-05-31', '2021-05-31', '2024-05-31']
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify application was created with education data
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        
        # Verify education data was properly parsed and saved
        self.assertEqual(len(application.education), 3)
        
        # Check first education entry
        self.assertEqual(application.education[0], {
            'school': 'MIT',
            'degree': 'BSc',
            'discipline': 'Computer Science',
            'start_date': '2015-09-01',
            'end_date': '2019-05-31'
        })
        
        # Check second education entry
        self.assertEqual(application.education[1], {
            'school': 'Stanford',
            'degree': 'MSc',
            'discipline': 'Software Engineering',
            'start_date': '2019-09-01',
            'end_date': '2021-05-31'
        })
        
        # Check third education entry
        self.assertEqual(application.education[2], {
            'school': 'Harvard',
            'degree': 'PhD',
            'discipline': 'AI',
            'start_date': '2021-09-01',
            'end_date': '2024-05-31'
        })

    def test_education_data_partial_submission(self):
        """Test handling of partial education data submission"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            'skills': 'Python, Django, Testing',
            # Submit partial education data
            'school[]': ['MIT'],
            'degree[]': ['BSc'],
            'discipline[]': ['Computer Science'],
            'start_date[]': ['2015-09-01'],
            'end_date[]': ['2019-05-31']
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify application was created with education data
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        
        # Verify single education entry was saved correctly
        self.assertEqual(len(application.education), 1)
        self.assertEqual(application.education[0], {
            'school': 'MIT',
            'degree': 'BSc',
            'discipline': 'Computer Science',
            'start_date': '2015-09-01',
            'end_date': '2019-05-31'
        })

    def test_education_data_empty_lists(self):
        """Test handling of empty education data lists"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            'skills': 'Python, Django, Testing',
            # Submit empty lists for education data
            'school[]': [],
            'degree[]': [],
            'discipline[]': [],
            'start_date[]': [],
            'end_date[]': []
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        self.assertEqual(len(application.education), 0)

    def test_work_experience_empty_lists(self):
        """Test handling of empty work experience data lists"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            'skills': 'Python, Django, Testing',
            # Submit empty lists for work experience
            'work_job_title[]': [],
            'work_employer[]': [],
            'work_start_date[]': [],
            'work_end_date[]': [],
            'job_description[]': []
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        self.assertEqual(len(application.work_experience), 0)

    def test_mixed_education_work_experience(self):
        """Test submission with both education and work experience data"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            'skills': 'Python, Django, Testing',
            # Education data
            'school[]': ['MIT', 'Stanford'],
            'degree[]': ['BSc', 'MSc'],
            'discipline[]': ['Computer Science', 'AI'],
            'start_date[]': ['2015-09-01', '2019-09-01'],
            'end_date[]': ['2019-05-31', '2021-05-31'],
            # Work experience data
            'work_job_title[]': ['Software Engineer', 'Lead Developer'],
            'work_employer[]': ['Google', 'Microsoft'],
            'work_start_date[]': ['2019-06-01', '2021-06-01'],
            'work_end_date[]': ['2021-05-31', '2023-05-31'],
            'job_description[]': ['Full-stack development', 'Team leadership']
        }
        
        response = self.client.post(
            reverse('apply_for_job', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        
        # Verify both education and work experience data
        self.assertEqual(len(application.education), 2)
        self.assertEqual(len(application.work_experience), 2)
        
        # Verify education data structure
        self.assertEqual(application.education[0], {
            'school': 'MIT',
            'degree': 'BSc',
            'discipline': 'Computer Science',
            'start_date': '2015-09-01',
            'end_date': '2019-05-31'
        })
        
        # Verify work experience data structure
        self.assertEqual(application.work_experience[0], {
            'work_job_title': 'Software Engineer',
            'work_employer': 'Google',
            'work_start_date': '2019-06-01',
            'work_end_date': '2021-05-31',
            'job_description': 'Full-stack development'
        })

    

    def test_applicants_application_education_parsing(self):
        """Test education data parsing in applicants_application view"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            # Education data arrays
            'school[]': ['MIT', 'Stanford'],
            'degree[]': ['BSc', 'MSc'],
            'discipline[]': ['Computer Science', 'AI'],
            'start_date[]': ['2015-09-01', '2019-09-01'],
            'end_date[]': ['2019-05-31', '2021-05-31']
        }
        
        response = self.client.post(
            reverse('applicants_application', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)  # Should redirect to job detail
        self.assertRedirects(response, reverse('job_detail', args=[self.job.id]))
        
        # Verify application was created
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        
        # Verify education data structure
        self.assertEqual(len(application.education), 2)
        self.assertEqual(application.education[0], {
            'school': 'MIT',
            'degree': 'BSc',
            'discipline': 'Computer Science',
            'start_date': '2015-09-01',
            'end_date': '2019-05-31'
        })

    def test_applicants_application_work_experience_parsing(self):
        """Test work experience data parsing in applicants_application view"""
        self.client.login(username='@testapplicant', password='testpass123')
        
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
            # Work experience data arrays
            'work_job_title[]': ['Software Engineer', 'Lead Developer'],
            'work_employer[]': ['Google', 'Microsoft'],
            'work_start_date[]': ['2019-06-01', '2021-06-01'],
            'work_end_date[]': ['2021-05-31', '2023-05-31'],
            'job_description[]': ['Full-stack development', 'Team leadership']
        }
        
        response = self.client.post(
            reverse('applicants_application', args=[self.job.id]),
            application_data,
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('job_detail', args=[self.job.id]))
        
        # Verify application was created
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        
        # Verify work experience data structure
        self.assertEqual(len(application.work_experience), 2)
        self.assertEqual(application.work_experience[0], {
            'work_job_title': 'Software Engineer',
            'work_employer': 'Google',
            'work_start_date': '2019-06-01',
            'work_end_date': '2021-05-31',
            'job_description': 'Full-stack development'
        })

    

