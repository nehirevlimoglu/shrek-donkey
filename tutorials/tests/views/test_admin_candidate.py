from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Job, Employer, Candidate
from django.utils import timezone
import json
from datetime import timedelta
from unittest.mock import patch
from django.core.exceptions import ValidationError
from tutorials.models.admin_models import Admin

User = get_user_model()

class AdminCandidateTests(TestCase):
    """Test suite for admin candidate management functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Clean up any existing data
        Candidate.objects.all().delete()
        Job.objects.all().delete()
        Employer.objects.all().delete()
        User.objects.all().delete()
        
        # Create admin user
        self.admin = Admin.objects.create_user(
            username='@testadmin',
            password='testpass123',
            email='admin@test.com',
            role='Admin'
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
            company_name='Test Company',
            company_location='Test Location',
            industry='Tech'
        )
        
        # Create job
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            company_name="Test Company",
            location="Test Location",
            description="Test Description",
            job_type="Full Time"
        )
        
        # Create candidate user
        self.candidate_user = User.objects.create_user(
            username='@testcandidate',
            password='testpass123',
            email='candidate@test.com',
            first_name='Test',
            last_name='Candidate',
            role='Applicant'
        )
        
        # Create candidate
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            job=self.job,
            application_date=timezone.now(),
            phone='1234567890',
            degree='Computer Science',
            school='Test University',
            skills='["Python", "Django", "JavaScript"]'
        )
        
        # Set up client and login as admin
        self.client = Client()
        self.client.login(username='@testadmin', password='testpass123')

    def tearDown(self):
        """Clean up after each test"""
        Candidate.objects.all().delete()
        Job.objects.all().delete()
        Employer.objects.all().delete()
        User.objects.all().delete()

    def test_get_candidate_info_success(self):
        """Test successful retrieval of candidate information"""
        response = self.client.get(
            reverse('get_candidate_info', args=[self.candidate.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        expected_data = {
            'id': self.candidate.id,
            'name': 'Test Candidate',  # from first_name and last_name in setUp
            'email': 'candidate@test.com',
            'application_date': self.candidate.application_date.strftime('%Y-%m-%d'),
            'status': 'Pending',  # default status
            'phone': '1234567890',
            'degree': 'Computer Science',
            'school': 'Test University',
            'skills': '["Python", "Django", "JavaScript"]'
        }
        
        # Verify all expected fields are present with correct values
        for key, value in expected_data.items():
            self.assertEqual(data[key], value)
        
        # Verify CORS headers
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        self.assertEqual(response["Access-Control-Allow-Methods"], "GET, OPTIONS")
        self.assertEqual(response["Access-Control-Allow-Headers"], "X-Requested-With, Content-Type")

    def test_get_candidate_info_not_found(self):
        """Test getting info for non-existent candidate"""
        response = self.client.get(
            reverse('get_candidate_info', args=[99999])
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': 'Candidate not found'}
        )

    def test_update_candidate_status_success(self):
        """Test successful status update"""
        data = {'status': 'Interview'}
        response = self.client.post(
            reverse('update_candidate_status', args=[self.candidate.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {'success': True})
        
        # Verify status was updated
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, 'Interview')

    def test_update_candidate_status_invalid_status(self):
        """Test updating with invalid status"""
        data = {'status': 'InvalidStatus'}
        response = self.client.post(
            reverse('update_candidate_status', args=[self.candidate.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertIn('error', response_data)
        self.assertIn('Valid options are', response_data['error'])

    def test_update_candidate_status_missing_status(self):
        """Test updating without providing status"""
        data = {}  # Empty data
        response = self.client.post(
            reverse('update_candidate_status', args=[self.candidate.id]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'error': 'Status is required'})

    def test_update_candidate_status_invalid_json(self):
        """Test updating with invalid JSON data"""
        response = self.client.post(
            reverse('update_candidate_status', args=[self.candidate.id]),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'error': 'Invalid JSON in request body'})

    def test_update_candidate_status_not_found(self):
        """Test updating non-existent candidate"""
        data = {'status': 'Interview'}
        response = self.client.post(
            reverse('update_candidate_status', args=[99999]),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.content), {'error': 'Candidate not found'})

    def test_get_candidate_info_with_missing_fields(self):
        """Test getting candidate info with missing optional fields"""
        # Create a candidate with minimal fields
        minimal_candidate = Candidate.objects.create(
            user=User.objects.create_user(
                username='@minimal',
                password='testpass123',
                email='minimal@test.com',
                role='Applicant'
            ),
            job=self.job,
            application_date=timezone.now()
        )
        
        response = self.client.get(
            reverse('get_candidate_info', args=[minimal_candidate.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify default values for missing fields
        self.assertEqual(data['phone'], 'Not provided')
        self.assertEqual(data['degree'], 'Not provided')
        self.assertEqual(data['school'], 'Not provided')
        self.assertEqual(data['skills'], '[]')

    def test_unauthorized_access(self):
        """Test access by non-admin user"""
        # Login as non-admin user
        self.client.login(username='@testemployer', password='testpass123')
        
        # Try to get candidate info
        response = self.client.get(
            reverse('get_candidate_info', args=[self.candidate.id])
        )
        self.assertEqual(response.status_code, 403)
        
        # Try to update candidate status
        response = self.client.post(
            reverse('update_candidate_status', args=[self.candidate.id]),
            data=json.dumps({'status': 'Interview'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    @patch('tutorials.models.employer_models.Candidate.objects.get')
    def test_get_candidate_info_unexpected_error(self, mock_get):
        """Test handling of unexpected errors when getting candidate info"""
        # Mock the get method to raise an unexpected error
        mock_get.side_effect = ValidationError("Unexpected database error")
        
        # Make the request
        response = self.client.get(
            reverse('get_candidate_info', args=[self.candidate.id])
        )
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Unexpected database error', data['error'])


    def test_get_candidate_info_database_error(self):
        """Test handling of database errors when getting candidate info"""
        with patch('tutorials.models.employer_models.Candidate.objects.get') as mock_get:
            # Simulate a database error
            mock_get.side_effect = Exception("Database connection failed")
            
            # Make the request
            response = self.client.get(
                reverse('get_candidate_info', args=[self.candidate.id])
            )
            
            # Verify response
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'Database connection failed')



    def test_update_candidate_status_unexpected_error(self):
        """Test handling of unexpected errors when updating candidate status"""
        with patch('tutorials.models.employer_models.Candidate.objects.get') as mock_get:
            # First mock the get to return our candidate
            mock_get.return_value = self.candidate
            
            # Then mock the save method to raise an unexpected error
            self.candidate.save = lambda: exec('raise Exception("Database connection lost")')
            
            # Make the request
            data = {'status': 'Interview'}
            response = self.client.post(
                reverse('update_candidate_status', args=[self.candidate.id]),
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Verify response
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'Database connection lost')

    def test_update_candidate_status_database_error(self):
        """Test handling of database errors when updating candidate status"""
        with patch('tutorials.models.employer_models.Candidate.objects.get') as mock_get:
            # Simulate a database error during save
            def raise_error(*args, **kwargs):
                raise Exception("Database deadlock detected")
            
            mock_candidate = self.candidate
            mock_candidate.save = raise_error
            mock_get.return_value = mock_candidate
            
            # Make the request
            data = {'status': 'Interview'}
            response = self.client.post(
                reverse('update_candidate_status', args=[self.candidate.id]),
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Verify response
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'Database deadlock detected')

    def test_update_candidate_status_validation_error(self):
        """Test handling of validation errors when updating candidate status"""
        with patch('tutorials.models.employer_models.Candidate.objects.get') as mock_get:
            # Mock the save method to raise a validation error
            def raise_validation_error(*args, **kwargs):
                raise ValidationError("Status transition not allowed")
            
            mock_candidate = self.candidate
            mock_candidate.save = raise_validation_error
            mock_get.return_value = mock_candidate
            
            # Make the request
            data = {'status': 'Interview'}
            response = self.client.post(
                reverse('update_candidate_status', args=[self.candidate.id]),
                data=json.dumps(data),
                content_type='application/json'
            )
            
            # Verify response
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertIn('error', data)
            self.assertIn('Status transition not allowed', data['error']) 