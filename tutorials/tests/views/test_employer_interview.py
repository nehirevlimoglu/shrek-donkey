from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from tutorials.models.employer_models import Employer, Job, Candidate, Interview
from tutorials.models.applicants_models import Applicant, ApplicantNotification
from tutorials.forms.employer_forms import InterviewForm
from django.contrib.messages import get_messages
from django.utils import timezone
import datetime

User = get_user_model()

class EmployerInterviewTests(TestCase):
    """Test suite for employer interview functionality"""

    def setUp(self):
        """Set up test data"""
        # Create employer user
        self.employer_user = User.objects.create_user(
            username="test_employer",
            password="password123",
            email="employer@example.com",
            role='Employer'
        )

        # Create employer profile
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="Test Location"
        )

        # Create applicant user
        self.applicant_user = User.objects.create_user(
            username="test_applicant",
            password="password123",
            email="applicant@example.com",
            first_name="John",
            last_name="Doe",
            role='Applicant'
        )

        # Create applicant profile - Fixed to match model fields
        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            degree='Computer Science',  # Added required field
            salary_preferences='80000-100000',  # Added required field
            location_preferences='Remote'  # Added required field
        )

        # Create a job
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Test job description",
            location="Test Location",
            job_type="Full Time",
            salary="100000",
            requirements="Python, Django",
            application_deadline=now().date() + timedelta(days=30)
        )

        # Create a candidate
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            first_name="John",
            last_name="Doe",
            application_date=now()
        )

        # Create an interview
        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=now().date() + timedelta(days=1),
            time="14:00:00",
            interview_link="https://meet.google.com/test",
            notes="Test interview notes"
        )

        self.client = Client()
        self.client.force_login(self.employer_user)

    def test_employer_calendar_view(self):
        """Test viewing employer calendar"""
        response = self.client.get(reverse('employer_calendar'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_calendar.html')
        self.assertIn('interviews', response.context)
        self.assertEqual(list(response.context['interviews']), [self.interview])

    
    def test_schedule_interview_get(self):
        """Test GET request to schedule interview page"""
        response = self.client.get(reverse('schedule_interview', args=[self.candidate.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'schedule_interview.html')
        self.assertEqual(response.context['applicant'], self.candidate)

    def test_schedule_interview_post_success(self):
        """Test successful interview scheduling"""
        tomorrow = timezone.now() + timedelta(days=1)
        interview_data = {
            'interview_date': tomorrow.strftime('%Y-%m-%d'),
            'interview_time': '15:00',
            'interview_link': 'https://meet.google.com/new-test',
            'notes': 'New interview notes'
        }
        
        response = self.client.post(
            reverse('schedule_interview', args=[self.candidate.id]),
            interview_data,
            follow=True
        )
        
        # Check redirect and message
        self.assertRedirects(response, reverse('employer_calendar'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Interview scheduled successfully!")

        # Verify interview was created
        interview = Interview.objects.get(
            candidate=self.candidate,
            job=self.job,
            interview_link='https://meet.google.com/new-test'
        )
        self.assertEqual(interview.notes, 'New interview notes')
        
        # Verify applicant notification was created
        notification = ApplicantNotification.objects.get(applicant=self.applicant)
        self.assertEqual(notification.title, "Interview Scheduled")
        self.assertIn(self.job.title, notification.message)
        self.assertIn('https://meet.google.com/new-test', notification.message)

    def test_schedule_interview_post_invalid_date(self):
        """Test scheduling interview with invalid date value"""
        invalid_data = {
            'interview_date': '2023-13-45',  # Invalid date value
            'interview_time': '14:00',
            'interview_link': 'https://meet.google.com/test',
            'notes': 'Test notes'
        }
        
        # Get initial count of interviews
        initial_count = Interview.objects.count()
        
        response = self.client.post(
            reverse('schedule_interview', args=[self.candidate.id]),
            invalid_data
        )
        
        # Verify response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Invalid date or time format.")
        
        # Verify no new interview was created
        self.assertEqual(Interview.objects.count(), initial_count)

    def test_interview_detail_view(self):
        """Test viewing interview details"""
        response = self.client.get(reverse('interview_detail', args=[self.interview.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'interview_detail.html')
        self.assertEqual(response.context['interview'], self.interview)

    def test_reschedule_interview(self):
        """Test rescheduling an interview"""
        new_date = (now().date() + timedelta(days=3)).strftime('%Y-%m-%d')
        new_time = '16:00'
        
        response = self.client.post(
            reverse('reschedule_interview', args=[self.interview.pk]),
            {'date': new_date, 'time': new_time},
            follow=True
        )
        
        self.assertRedirects(response, reverse('interview_detail', args=[self.interview.pk]))
        
        # Verify interview was updated
        self.interview.refresh_from_db()
        self.assertEqual(self.interview.time.strftime('%H:%M'), '16:00')

    def test_get_interviews_json(self):
        """Test getting interviews as JSON for calendar"""
        response = self.client.get(reverse('get_interview_events'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.interview.pk)
        self.assertEqual(
            data[0]['title'], 
            f"Interview: {self.candidate.first_name} {self.candidate.last_name}"
        )
        self.assertTrue('start' in data[0])
        self.assertTrue('url' in data[0])

   

    def test_schedule_interview_nonexistent_candidate(self):
        """Test scheduling interview for non-existent candidate"""
        response = self.client.get(reverse('schedule_interview', args=[99999]))
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode(), "Candidate does not exist.")

    def test_create_interview_event(self):
        """Test creating an interview event"""
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        response = self.client.post(
            reverse('schedule_interview', args=[self.candidate.id]),
            {
                'interview_date': tomorrow.strftime('%Y-%m-%d'),
                'interview_time': '10:00',
                'interview_link': 'https://meet.google.com/test',
                'notes': 'Test interview notes'
            }
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('employer_calendar'))
        
        # Verify interview was created
        new_interview = Interview.objects.filter(
            candidate=self.candidate,
            date=tomorrow.date(),
            time='10:00:00'
        ).exists()
        self.assertTrue(new_interview)

    

    def test_get_interviews_employer_not_found(self):
        """Test getting interviews when employer profile doesn't exist"""
        # Create a user without an employer profile
        user_without_employer = User.objects.create_user(
            username="no_employer",
            password="password123",
            email="no_employer@example.com",
            role='Employer'
        )
        
        # Login as the user without employer profile
        self.client.force_login(user_without_employer)
        
        # Make the request
        response = self.client.get(reverse('get_interview_events'))
        
        # Check response
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"error": "Employer not found"}
        )

    def test_schedule_interview_success(self):
        """Test successful interview scheduling"""
        tomorrow = now().date() + timedelta(days=1)
        interview_data = {
            'interview_date': tomorrow.strftime('%Y-%m-%d'),
            'interview_time': '15:00',
            'interview_link': 'https://meet.google.com/new-test',
            'notes': 'New interview notes'
        }
        
        # Delete any existing interviews to avoid MultipleObjectsReturned
        Interview.objects.all().delete()
        
        response = self.client.post(
            reverse('schedule_interview', args=[self.candidate.id]),
            interview_data,
            follow=True
        )
        
        # Check redirect and message
        self.assertRedirects(response, reverse('employer_calendar'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Interview scheduled successfully!")

        # Verify interview was created
        interview = Interview.objects.get(
            candidate=self.candidate,
            job=self.job,
            interview_link='https://meet.google.com/new-test'
        )
        self.assertEqual(interview.notes, 'New interview notes')
        self.assertEqual(interview.date, tomorrow)
        self.assertEqual(interview.time.strftime('%H:%M'), '15:00')
        
        # Verify notification was created
        notification = ApplicantNotification.objects.get(applicant=self.applicant)
        self.assertEqual(notification.title, "Interview Scheduled")
        self.assertIn(self.job.title, notification.message)
        self.assertIn('https://meet.google.com/new-test', notification.message)
        self.assertIn('New interview notes', notification.message)

    def test_schedule_interview_invalid_date(self):
        """Test scheduling interview with invalid date format"""
        invalid_data = {
            'interview_date': 'not-a-date',  # Invalid date format
            'interview_time': '14:00',
            'interview_link': 'https://meet.google.com/test',
            'notes': 'Test notes'
        }
        
        # Get initial count of interviews
        initial_count = Interview.objects.count()
        
        try:
            response = self.client.post(
                reverse('schedule_interview', args=[self.candidate.id]),
                invalid_data
            )
            
            # Verify response
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), "Invalid date or time format.")
            
            # Verify no new interview was created
            self.assertEqual(Interview.objects.count(), initial_count)
        except Exception as e:
            self.fail(f"Test failed with exception: {str(e)}")

    def test_schedule_interview_invalid_time(self):
        """Test scheduling interview with invalid time format"""
        tomorrow = now().date() + timedelta(days=1)
        invalid_data = {
            'interview_date': tomorrow.strftime('%Y-%m-%d'),
            'interview_time': 'not-a-time',  # Invalid time format
            'interview_link': 'https://meet.google.com/test',
            'notes': 'Test notes'
        }
        
        # Get initial count of interviews
        initial_count = Interview.objects.count()
        
        try:
            response = self.client.post(
                reverse('schedule_interview', args=[self.candidate.id]),
                invalid_data
            )
            
            # Verify response
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content.decode(), "Invalid date or time format.")
            
            # Verify no new interview was created
            self.assertEqual(Interview.objects.count(), initial_count)
        except Exception as e:
            self.fail(f"Test failed with exception: {str(e)}")

    def test_schedule_interview_no_applicant_profile(self):
        """Test scheduling interview for candidate without applicant profile"""
        # Create a new candidate without an associated applicant profile
        user = User.objects.create_user(
            username="no_profile",
            password="pass123",
            email="no_profile@example.com",
            role='Applicant'
        )
        candidate = Candidate.objects.create(
            user=user,
            job=self.job,
            first_name="No",
            last_name="Profile",
            application_date=now()
        )
        
        tomorrow = now().date() + timedelta(days=1)
        interview_data = {
            'interview_date': tomorrow.strftime('%Y-%m-%d'),
            'interview_time': '15:00',
            'interview_link': 'https://meet.google.com/test',
            'notes': 'Test notes'
        }
        
        response = self.client.post(
            reverse('schedule_interview', args=[candidate.id]),
            interview_data,
            follow=True
        )
        
        # Should still create interview but log warning about notification
        self.assertRedirects(response, reverse('employer_calendar'))
        
        # Verify interview was created
        self.assertTrue(
            Interview.objects.filter(
                candidate=candidate,
                interview_link='https://meet.google.com/test'
            ).exists()
        )
        
        # Verify no notification was created
        self.assertFalse(
            ApplicantNotification.objects.filter(
                title="Interview Scheduled"
            ).exists()
        )

