from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tutorials.models.employer_models import Employer, Job, Candidate, Interview, EmployerEvent
from tutorials.models.applicants_models import Applicant
from datetime import timedelta

User = get_user_model()

class EmployerInterviewEventTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create employer user
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            role='Employer'
        )
        
        # Create employer profile
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username='@testemployer',
            email='employer@test.com',
            company_name='Test Company',
            company_location='Test Location',
            industry='Tech'
        )

        # Create applicant user
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            role='Applicant'
        )

        # Create job
        self.job = Job.objects.create(
            employer=self.employer,
            title='Software Engineer',
            description='Test job',
            location='Test Location',
            salary=100000
        )

        # Create candidate
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            first_name='Test',
            last_name='Candidate'
        )

        self.client = Client()
        self.client.login(username='@testemployer', password='testpass123')
        self.url = reverse('schedule_interview', args=[self.candidate.id])

    def test_create_interview_event_success(self):
        """Test successful creation of an interview event"""
        tomorrow = timezone.now() + timedelta(days=1)
        data = {
            'interview_date': tomorrow.strftime('%Y-%m-%d'),
            'interview_time': '10:00',
            'interview_link': 'https://meet.google.com/test',
            'notes': 'Test interview'
        }
        
        response = self.client.post(self.url, data)
        
        # Should redirect to employer calendar after success
        self.assertRedirects(response, reverse('employer_calendar'))
        
        # Verify interview was created
        interview = Interview.objects.latest('date')
        self.assertEqual(interview.candidate, self.candidate)
        self.assertEqual(interview.job, self.job)
        self.assertEqual(interview.time.strftime('%H:%M'), '10:00')

    def test_create_interview_event_invalid_candidate(self):
        """Test interview creation with invalid candidate ID"""
        url = reverse('schedule_interview', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_create_interview_event_unauthorized(self):
        """Test interview creation by unauthorized user"""
        self.client.logout()
        self.client.login(username='@testapplicant', password='testpass123')
        
        tomorrow = timezone.now() + timedelta(days=1)
        data = {
            'interview_date': tomorrow.strftime('%Y-%m-%d'),
            'interview_time': '10:00',
            'interview_link': 'https://meet.google.com/test',
            'notes': 'Test interview'
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)  # Forbidden

    def test_create_interview_event_overlapping(self):
        """Test creation of overlapping interview events"""
        # Create first interview
        tomorrow = timezone.now() + timedelta(days=1)
        data = {
            'interview_date': tomorrow.strftime('%Y-%m-%d'),
            'interview_time': '10:00',
            'interview_link': 'https://meet.google.com/test1',
            'notes': 'First interview'
        }
        self.client.post(self.url, data)

        # Try to create second interview at same time
        data['interview_link'] = 'https://meet.google.com/test2'
        response = self.client.post(self.url, data)
        
        # Should still succeed as we don't currently check for overlaps
        self.assertRedirects(response, reverse('employer_calendar')) 