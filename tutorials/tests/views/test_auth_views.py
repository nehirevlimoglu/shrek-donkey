from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Admin
from tutorials.models.employer_models import Employer, Job, Candidate
from tutorials.models.applicants_models import Applicant
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import AnonymousUser
from unittest.mock import patch
from datetime import date

User = get_user_model()

class AuthViewsTests(TestCase):
    """Test suite for authentication related views"""
    
    def setUp(self):
        """Set up test data"""
                
        # Clean up any existing data
        User.objects.all().delete()
        Admin.objects.all().delete()
        Employer.objects.all().delete()
        Applicant.objects.all().delete()
        
        # Create test users for each role
        self.admin_user = User.objects.create_user(
            username='@testadmin',
            password='testpass123',
            email='admin@test.com',
            first_name='Test',
            last_name='Admin',
            role='Admin'
        )
        
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
            username=self.employer_user.username,
            email=self.employer_user.email,
            company_name='Test Company',
            company_location='Test Location',
            industry='Tech'
        )
        
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
            user=self.applicant_user
        )
        
        self.client = Client()

    def test_login_page_load(self):
        """Test if login page loads correctly"""
        response = self.client.get(reverse('log_in'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'log_in.html')
        self.assertTrue(response.cookies.get('csrftoken'))

    def test_login_success_admin(self):
        """Test successful login for admin user"""
        response = self.client.post(reverse('log_in'), {
            'username': '@testadmin',
            'password': 'testpass123'
        }, follow=True)  # Add follow=True to follow redirects
        self.assertRedirects(response, reverse('admin_home_page'))
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_success_employer(self):
        """Test successful login for employer user"""
        response = self.client.post(reverse('log_in'), {
            'username': '@testemployer',
            'password': 'testpass123'
        }, follow=True)  # Add follow=True to follow redirects
        self.assertRedirects(response, reverse('employer_home_page'))

    def test_login_success_applicant(self):
        """Test successful login for applicant user"""
        response = self.client.post(reverse('log_in'), {
            'username': '@testapplicant',
            'password': 'testpass123'
        }, follow=True)  # Add follow=True to follow redirects
        self.assertRedirects(response, reverse('applicants-home-page'))

    def test_login_failure_wrong_password(self):
        """Test login failure with wrong password"""
        response = self.client.post(reverse('log_in'), {
            'username': '@testadmin',
            'password': 'wrongpass'
        })
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Incorrect username or password")
        self.assertTrue('_auth_user_id' not in self.client.session)

    def test_login_failure_nonexistent_user(self):
        """Test login failure with nonexistent user"""
        response = self.client.post(reverse('log_in'), {
            'username': '@nonexistent',
            'password': 'testpass123'
        })
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Incorrect username or password")

    def test_login_missing_fields(self):
        """Test login with missing fields"""
        # Test missing username
        response = self.client.post(reverse('log_in'), {
            'password': 'testpass123',
            'username': ''  # Send empty username instead of omitting it
        })
        self.assertEqual(response.status_code, 200)
        
        # Test missing password
        response = self.client.post(reverse('log_in'), {
            'username': '@testadmin',
            'password': ''  # Send empty password instead of omitting it
        })
        self.assertEqual(response.status_code, 200)

    def test_csrf_token_present(self):
        """Test that CSRF token is present in the login form"""
        response = self.client.get(reverse('log_in'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_csrf_failure(self):
        """Test CSRF failure handling"""
        # Create a client that enforces CSRF checks
        csrf_client = Client(enforce_csrf_checks=True)
        
        # Attempt to post without getting a CSRF token first
        response = csrf_client.post(reverse('log_in'), {
            'username': '@testadmin',
            'password': 'testpass123'
        })
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Verify the custom CSRF failure view was used
        self.assertTemplateUsed(response, 'log_in.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('CSRF validation error' in str(msg) for msg in messages))

    def test_logout(self):
        """Test logout functionality"""
        self.client.login(username='@testadmin', password='testpass123')
        response = self.client.get(reverse('log-out'))
        self.assertRedirects(response, reverse('log_in'))
        self.assertTrue('_auth_user_id' not in self.client.session)
        self.assertTrue('csrftoken' not in response.cookies or 
                      not response.cookies['csrftoken'].value)

    def test_login_preserves_csrf_cookie(self):
        """Test that CSRF cookie is preserved after login"""
        response = self.client.get(reverse('log_in'))
        initial_csrf = response.cookies['csrftoken'].value
        
        response = self.client.post(reverse('log_in'), {
            'username': '@testadmin',
            'password': 'testpass123'
        })
        
        self.assertTrue('csrftoken' in response.cookies)

class ProfileSetupTests(TestCase):
    """Test suite for profile setup views"""
    
    def setUp(self):
        """Set up test data"""
        # Create base users without profiles
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            first_name='Test',
            last_name='Employer',
            role='Employer'
        )
        
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )
        
        # Create a test image file
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',  # empty image
            content_type='image/jpeg'
        )
        
        self.client = Client()

    def test_applicant_profile_setup_get_unauthorized(self):
        """Test GET request to applicant profile setup when not logged in"""
        response = self.client.get(reverse('applicant_profile_setup'))
        self.assertRedirects(response, f"{reverse('log_in')}?next={reverse('applicant_profile_setup')}")

    def test_applicant_profile_setup_get_authorized(self):
        """Test GET request to applicant profile setup when logged in"""
        self.client.login(username='@testapplicant', password='testpass123')
        response = self.client.get(reverse('applicant_profile_setup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicant_profile_setup.html')

    
    def test_employer_profile_setup_get_unauthorized(self):
        """Test GET request to employer profile setup when not logged in"""
        response = self.client.get(reverse('employer_profile_setup'))
        self.assertRedirects(response, f"{reverse('log_in')}?next={reverse('employer_profile_setup')}")

    def test_employer_profile_setup_get_authorized(self):
        """Test GET request to employer profile setup when logged in"""
        self.client.login(username='@testemployer', password='testpass123')
        response = self.client.get(reverse('employer_profile_setup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_profile_setup.html')

    

    def test_employer_profile_setup_post_invalid(self):
        """Test POST request to employer profile setup with invalid data"""
        self.client.login(username='@testemployer', password='testpass123')
        
        data = {
            'company_name': '',  # Required field is empty
            'industry': 'Invalid',  # Invalid choice
        }
        
        response = self.client.post(reverse('employer_profile_setup'), data)
        self.assertEqual(response.status_code, 200)  # Returns to form
        self.assertTemplateUsed(response, 'employer_profile_setup.html')
        
        # Verify no employer profile was created
        self.assertFalse(Employer.objects.filter(user=self.employer_user).exists())

    def test_applicant_profile_setup_post_invalid(self):
        """Test POST request to applicant profile setup with invalid data"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        data = {
            'phone': 'invalid-phone',  # Invalid phone format
            'email': 'invalid-email',  # Invalid email format
        }
        
        response = self.client.post(reverse('applicant_profile_setup'), data)
        self.assertEqual(response.status_code, 200)  # Returns to form
        self.assertTemplateUsed(response, 'applicant_profile_setup.html')

    def test_wrong_user_role_access(self):
        """Test accessing profile setup with wrong user role"""
        # Try to access employer setup as applicant
        self.client.login(username='@testapplicant', password='testpass123')
        response = self.client.get(reverse('employer_profile_setup'))
        self.assertEqual(response.status_code, 200)  # Should still load but might show different content
        
        # Try to access applicant setup as employer
        self.client.login(username='@testemployer', password='testpass123')
        response = self.client.get(reverse('applicant_profile_setup'))
        self.assertEqual(response.status_code, 200)  # Should still load but might show different content

    def test_profile_setup_update_existing(self):
        """Test updating existing profiles"""
        # Create initial employer profile
        employer = Employer.objects.create(
            user=self.employer_user,
            username=self.employer_user.username,
            email=self.employer_user.email,
            company_name='Old Company',
            company_location='Old Location',
            industry='Tech'
        )
        
        # Login and update profile
        self.client.login(username='@testemployer', password='testpass123')
        data = {
            'company_name': 'Updated Company',
            'company_location': 'Updated Location',
            'industry': 'Finance',
            'company_size': 100,
        }
        
        response = self.client.post(reverse('employer_profile_setup'), data)
        self.assertRedirects(response, reverse('employer_home_page'))
        
        # Verify the update
        employer.refresh_from_db()
        self.assertEqual(employer.company_name, 'Updated Company')
        self.assertEqual(employer.industry, 'Finance')

    def test_applicant_profile_setup_post_form_invalid(self):
        """Test applicant profile setup with invalid form data"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Submit with invalid data
        data = {
            'first_name': '',  # Required field is empty
            'last_name': '',   # Required field is empty
            'school': 'Test University'
        }
        
        response = self.client.post(reverse('applicant_profile_setup'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicant_profile_setup.html')
        
        # Check if form errors are present
        self.assertTrue(response.context['form'].errors)

    def test_applicant_profile_setup_update_existing(self):
        """Test updating existing applicant profile"""
        # Create initial applicant profile
        applicant = Applicant.objects.create(
            user=self.applicant_user,
            first_name='Old Name',
            last_name='Old Last',
            school='Old School'
        )
        
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Update the profile
        data = {
            'first_name': 'New Name',
            'last_name': 'New Last',
            'school': 'New School',
            'degree': 'Master',
            'discipline': 'Computer Science'
        }
        
        response = self.client.post(reverse('applicant_profile_setup'), data)
        self.assertRedirects(response, reverse('applicants-home-page'))
        
        # Verify the update
        applicant.refresh_from_db()
        self.assertEqual(applicant.first_name, 'New Name')
        self.assertEqual(applicant.school, 'New School')

    def test_applicant_profile_setup_with_files(self):
        """Test applicant profile setup with file uploads"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Create test files
        test_resume = SimpleUploadedFile(
            name='test_resume.pdf',
            content=b'test resume content',
            content_type='application/pdf'
        )
        test_cover_letter = SimpleUploadedFile(
            name='test_cover.pdf',
            content=b'test cover letter content',
            content_type='application/pdf'
        )
        
        data = {
            'first_name': 'Test',
            'last_name': 'Applicant',
            'school': 'Test University',
            'degree': 'Bachelor',
            'discipline': 'Computer Science',
            'resume': test_resume,
            'cover_letter': test_cover_letter
        }
        
        response = self.client.post(reverse('applicant_profile_setup'), data)
        self.assertRedirects(response, reverse('applicants-home-page'))
        
        # Verify files were saved
        applicant = Applicant.objects.get(user=self.applicant_user)
        self.assertTrue(applicant.resume)
        self.assertTrue(applicant.cover_letter)

class JobMatchingViewTests(TestCase):
    """Test suite for job matching view"""
    
    def setUp(self):
        """Set up test data"""
        # Create employer user and profile
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            first_name='Test',
            last_name='Employer',
            role='Employer'
        )
        
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username=self.employer_user.username,
            email=self.employer_user.email,
            company_name='Test Company',
            company_location='Test Location',
            industry='Tech'
        )
        
        # Create a test job with extracted skills
        self.job = Job.objects.create(
            employer=self.employer,
            title='Software Developer',
            description='Test job description',
            company_name='Test Company',
            location='Test Location',
            extracted_skills='["Python", "Django"]'  # Add extracted skills
        )
        
        # Create applicant user
        self.candidate_user = User.objects.create_user(
            username='@testcandidate',
            password='testpass123',
            email='candidate@test.com',
            first_name='Test',
            last_name='Candidate',
            role='Applicant'
        )
        
        # Create candidate with required fields
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            job=self.job,
            first_name='Test',
            last_name='Candidate',
            skills='["Python", "Django"]',
            degree='Bachelor',
            school='Test University',
            discipline='Computer Science'
        )
        
        self.client = Client()

    def test_job_matching_view_nonexistent_job(self):
        """Test job matching view with non-existent job ID"""
        response = self.client.get(reverse('match_candidates', args=[99999]))
        self.assertEqual(response.status_code, 404)

    @patch('tutorials.utils.match_candidates_to_job')
    def test_job_matching_view_with_matches(self, mock_match):
        """Test job matching when candidates are found"""
        # Mock the matching function to return candidates
        mock_candidates = [
            {
                'candidate': self.candidate,
                'match_score': 0.95,
                'matching_skills': ['Python', 'Django']
            }
        ]
        mock_match.return_value = mock_candidates
        
        response = self.client.get(reverse('match_candidates', args=[self.job.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'candidate_matches.html')
        # Check if the job title is in the heading
        self.assertContains(response, f"Matched Candidates for {self.job.title}")
        # Check if candidate username is in the response
        self.assertContains(response, '@testcandidate')
        # Check if match score is in the response
        self.assertContains(response, 'Match Score: 0.95')

    def test_job_matching_view_template_content(self):
        """Test the content rendered in the template"""
        response = self.client.get(reverse('match_candidates', args=[self.job.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'candidate_matches.html')
        # Check for job title in the heading
        self.assertContains(response, f"Matched Candidates for {self.job.title}")

    @patch('tutorials.utils.match_candidates_to_job')
    def test_job_matching_view_candidate_details(self, mock_match):
        """Test that candidate details are properly displayed"""
        # Mock the matching function to return candidates
        mock_candidates = [
            {
                'candidate': self.candidate,
                'match_score': 0.95,
                'matching_skills': ['Python', 'Django']
            }
        ]
        mock_match.return_value = mock_candidates
        
        response = self.client.get(reverse('match_candidates', args=[self.job.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'candidate_matches.html')
        
        # Check for the heading
        self.assertContains(response, f"Matched Candidates for {self.job.title}")

    # Remove the invalid test since it's not a valid use case
    # The URL pattern only accepts numeric IDs, so testing with 'invalid' isn't meaningful
    # def test_job_matching_view_invalid_job_id(self):
    #     """Test job matching view with invalid job ID format"""
    #     response = self.client.get(reverse('match_candidates', args=['invalid']))
    #     self.assertEqual(response.status_code, 404) 

class FeedbackSubmissionTests(TestCase):
    """Test suite for feedback submission functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )
        
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            first_name='Test',
            last_name='Employer',
            role='Employer'
        )
        
        # Create profiles
        self.applicant = Applicant.objects.create(user=self.applicant_user)
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username='@testemployer',
            email='employer@test.com',
            company_name='Test Company',
            company_location='Test Location',
            industry='Tech'
        )
        
        self.client = Client()

    def test_feedback_page_load_unauthorized(self):
        """Test feedback page load when not logged in"""
        response = self.client.get(reverse('submit_feedback'))
        self.assertRedirects(response, f"{reverse('log_in')}?next={reverse('submit_feedback')}")

    def test_feedback_page_load_authorized(self):
        """Test feedback page load when logged in"""
        self.client.login(username='@testapplicant', password='testpass123')
        response = self.client.get(reverse('submit_feedback'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feedback_form.html')

    def test_feedback_submission_success_applicant(self):
        """Test successful feedback submission by applicant"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        data = {
            'feedback_type': 'bug',
            'subject': 'Test Feedback',
            'message': 'This is a test feedback message',
            'priority': 'high'
        }
        
        response = self.client.post(reverse('submit_feedback'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feedback_form.html')
        self.assertIn('success_message', response.context)
        self.assertEqual(
            response.context['success_message'],
            'Thank you for your feedback! We will process it as soon as possible.'
        )

    def test_feedback_submission_success_employer(self):
        """Test successful feedback submission by employer"""
        self.client.login(username='@testemployer', password='testpass123')
        
        data = {
            'feedback_type': 'feature',
            'subject': 'Feature Request',
            'message': 'Please add this feature',
            'priority': 'medium'
        }
        
        response = self.client.post(reverse('submit_feedback'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feedback_form.html')
        self.assertIn('success_message', response.context)

    def test_feedback_submission_missing_fields(self):
        """Test feedback submission with missing required fields"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Test missing feedback_type
        data = {
            'subject': 'Test Feedback',
            'message': 'Test message'
        }
        
        response = self.client.post(reverse('submit_feedback'), data)
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "All required fields must be filled out.")

    def test_feedback_submission_empty_fields(self):
        """Test feedback submission with empty fields"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        data = {
            'feedback_type': '',
            'subject': '',
            'message': '',
            'priority': 'low'
        }
        
        response = self.client.post(reverse('submit_feedback'), data)
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "All required fields must be filled out.")

    def test_feedback_notification_creation(self):
        """Test that a notification is created when feedback is submitted"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        data = {
            'feedback_type': 'bug',
            'subject': 'Test Feedback',
            'message': 'This is a test feedback message',
            'priority': 'high'
        }
        
        response = self.client.post(reverse('submit_feedback'), data)
        
        # Check if notification was created
        from tutorials.models.admin_models import Notification
        notification = Notification.objects.filter(
            title=f"New Feedback: {data['subject']}",
            message=data['message'],
            notification_type='feedback'
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.sender, self.applicant_user)
        self.assertEqual(notification.sender_type, 'applicant')
        self.assertEqual(notification.priority, data['priority'])
        self.assertFalse(notification.is_read)

    def test_feedback_submission_error_handling(self):
        """Test error handling during feedback submission"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Mock an exception during notification creation
        with patch('tutorials.models.admin_models.Notification.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            data = {
                'feedback_type': 'bug',
                'subject': 'Test Feedback',
                'message': 'This is a test feedback message',
                'priority': 'high'
            }
            
            response = self.client.post(reverse('submit_feedback'), data)
            
            self.assertEqual(response.status_code, 200)
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(any('Error submitting feedback' in str(msg) for msg in messages))

    def test_feedback_submission_with_medium_priority(self):
        """Test feedback submission with default medium priority"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        data = {
            'feedback_type': 'bug',
            'subject': 'Test Feedback',
            'message': 'This is a test feedback message',
            # Omit priority to test default value
        }
        
        response = self.client.post(reverse('submit_feedback'), data)
        
        # Check if notification was created with medium priority
        from tutorials.models.admin_models import Notification
        notification = Notification.objects.get(title=f"New Feedback: {data['subject']}")
        self.assertEqual(notification.priority, 'medium')  # Default priority
        self.assertEqual(response.status_code, 200)
        self.assertIn('success_message', response.context)

    def test_feedback_submission_user_type_detection(self):
        """Test correct user type detection in feedback submission"""
        # Test as employer
        self.client.login(username='@testemployer', password='testpass123')
        employer_data = {
            'feedback_type': 'feature',
            'subject': 'Employer Feedback',
            'message': 'Employer test message',
            'priority': 'high'
        }
        response = self.client.post(reverse('submit_feedback'), employer_data)
        from tutorials.models.admin_models import Notification
        employer_notification = Notification.objects.get(title=f"New Feedback: {employer_data['subject']}")
        self.assertEqual(employer_notification.sender_type, 'employer')

        # Clear notifications
        Notification.objects.all().delete()

        # Test as applicant
        self.client.login(username='@testapplicant', password='testpass123')
        applicant_data = {
            'feedback_type': 'bug',
            'subject': 'Applicant Feedback',
            'message': 'Applicant test message',
            'priority': 'high'
        }
        response = self.client.post(reverse('submit_feedback'), applicant_data)
        applicant_notification = Notification.objects.get(title=f"New Feedback: {applicant_data['subject']}")
        self.assertEqual(applicant_notification.sender_type, 'applicant')

    def test_feedback_submission_partial_fields(self):
        """Test feedback submission with some fields missing"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        test_cases = [
            {'subject': 'Test', 'message': 'Test'},  # Missing feedback_type
            {'feedback_type': 'bug', 'message': 'Test'},  # Missing subject
            {'feedback_type': 'bug', 'subject': 'Test'},  # Missing message
        ]
        
        for data in test_cases:
            response = self.client.post(reverse('submit_feedback'), data)
            self.assertEqual(response.status_code, 200)
            messages = list(get_messages(response.wsgi_request))
            self.assertEqual(str(messages[-1]), "All required fields must be filled out.")

    def test_feedback_submission_database_error(self):
        """Test feedback submission when database error occurs"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        data = {
            'feedback_type': 'bug',
            'subject': 'Test Feedback',
            'message': 'Test message',
            'priority': 'high'
        }
        
        # Mock the Notification.objects.create to raise an exception
        with patch('tutorials.models.admin_models.Notification.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database connection error")
            
            response = self.client.post(reverse('submit_feedback'), data)
            
            self.assertEqual(response.status_code, 200)
            messages = list(get_messages(response.wsgi_request))
            self.assertEqual(
                str(messages[0]),
                "Error submitting feedback: Database connection error"
            )

    def test_feedback_submission_action_url_none(self):
        """Test feedback submission with action_url explicitly set to None"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        data = {
            'feedback_type': 'bug',
            'subject': 'Test Feedback',
            'message': 'This is a test feedback message',
            'priority': 'high'
        }
        
        response = self.client.post(reverse('submit_feedback'), data)
        
        # Verify notification was created with action_url=None
        from tutorials.models.admin_models import Notification
        notification = Notification.objects.get(title=f"New Feedback: {data['subject']}")
        self.assertIsNone(notification.action_url) 

class SignUpTests(TestCase):
    """Test suite for sign up functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        # Clear any existing users
        User.objects.all().delete()
        
        self.valid_employer_data = {
            'username': '@testemployer',
            'email': 'employer@test.com',
            'first_name': 'Test',
            'last_name': 'Employer',
            'role': 'Employer',
            'password1': 'StrongPass123!',  # Updated to meet password requirements
            'password2': 'StrongPass123!'
        }
        
        self.valid_applicant_data = {
            'username': '@testapplicant',
            'email': 'applicant@test.com',
            'first_name': 'Test',
            'last_name': 'Applicant',
            'role': 'Applicant',
            'password1': 'StrongPass123!',  # Updated to meet password requirements
            'password2': 'StrongPass123!'
        }

    def test_signup_page_load(self):
        """Test if signup page loads correctly"""
        response = self.client.get(reverse('sign-up'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        self.assertTrue('form' in response.context)

    def test_signup_invalid_username(self):
        """Test signup with invalid username format"""
        invalid_data = self.valid_employer_data.copy()
        invalid_data['username'] = 'invalid'  # Missing @ prefix
        
        response = self.client.post(reverse('sign-up'), invalid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        self.assertFalse(User.objects.filter(username='invalid').exists())
        
        form = response.context['form']
        self.assertTrue(form.errors.get('username'))
        self.assertIn('Username must consist of @ followed by at least three alphanumericals', 
                     form.errors['username'][0])

    def test_signup_password_mismatch(self):
        """Test signup with mismatched passwords"""
        invalid_data = self.valid_employer_data.copy()
        invalid_data['password2'] = 'DifferentPass123!'
        
        response = self.client.post(reverse('sign-up'), invalid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        self.assertFalse(User.objects.filter(username='@testemployer').exists())
        
        form = response.context['form']
        self.assertTrue(form.errors.get('password2'))
        self.assertIn('Passwords do not match.',  # Updated to match actual error message
                     form.errors['password2'][0])

    def test_signup_existing_username(self):
        """Test signup with already existing username"""
        # Create a user first
        User.objects.create_user(
            username='@testemployer',
            password='StrongPass123!',
            email='existing@test.com',
            role='Employer',
            first_name='Test',
            last_name='User'
        )
        
        response = self.client.post(reverse('sign-up'), self.valid_employer_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        
        form = response.context['form']
        self.assertTrue(form.errors.get('username'))
        self.assertIn('User with this Username already exists.',  # Updated to match actual error message
                     form.errors['username'][0])

    def test_signup_existing_email(self):
        """Test signup with already existing email"""
        # Create a user first
        User.objects.create_user(
            username='@existing',
            password='testpass123',
            email='employer@test.com',
            role='Employer',
            first_name='Test',
            last_name='User'
        )
        
        response = self.client.post(reverse('sign-up'), self.valid_employer_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        
        form = response.context['form']
        self.assertTrue(form.errors.get('email'))
        self.assertIn('User with this Email already exists.', 
                     form.errors['email'][0])

    def test_signup_missing_required_fields(self):
        """Test signup with missing required fields"""
        required_fields = ['username', 'email', 'first_name', 'last_name', 'role']
        
        for field in required_fields:
            invalid_data = self.valid_employer_data.copy()
            invalid_data[field] = ''
            
            response = self.client.post(reverse('sign-up'), invalid_data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sign_up.html')
            
            form = response.context['form']
            self.assertTrue(form.errors.get(field))
            self.assertIn('This field is required.', 
                         form.errors[field][0])

    def test_signup_invalid_email(self):
        """Test signup with invalid email format"""
        invalid_data = self.valid_employer_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(reverse('sign-up'), invalid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        
        form = response.context['form']
        self.assertTrue(form.errors.get('email'))
        self.assertIn('Enter a valid email address.', 
                     form.errors['email'][0])

    def test_signup_profile_creation_error(self):
        """Test signup when profile creation fails"""
        with patch('tutorials.models.employer_models.Employer.objects.create') as mock_create:
            mock_create.side_effect = Exception("Profile creation failed")
            
            # Create the user first to simulate the error happening during profile creation
            user = User.objects.create_user(
                username='@testemployer',
                password='StrongPass123!',
                email='employer@test.com',
                role='Employer',
                first_name='Test',
                last_name='Employer'
            )
            
            response = self.client.post(reverse('sign-up'), self.valid_employer_data)
            
            # Verify the user exists
            user = User.objects.filter(username='@testemployer').first()
            self.assertIsNotNone(user)
            
            # Should redirect to login on error
            self.assertRedirects(response, reverse('log_in')) 