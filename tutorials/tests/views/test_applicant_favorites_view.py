from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.applicants_models import Applicant
from tutorials.models.employer_models import Job, Employer
from django.http import JsonResponse
import json

User = get_user_model()

class ApplicantFavoritesTests(TestCase):
    """Test suite for applicant favorites functionality"""
    
    def setUp(self):
        """Set up test data for favorites tests"""
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
            salary_preferences='80000-100000',
            location_preferences='Remote'
        )

        # Create employer user and profile
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            role='Employer'
        )
        
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='Test Company'
        )

        # Create test jobs
        self.job1 = Job.objects.create(
            employer=self.employer,
            title='Software Engineer',
            company_name='Test Company',
            location='Remote',
            description='Test Description 1',
            status='approved'
        )

        self.job2 = Job.objects.create(
            employer=self.employer,
            title='Data Scientist',
            company_name='Test Company',
            location='Remote',
            description='Test Description 2',
            status='approved'
        )
        
        # Set up test client
        self.client = Client()

    def test_view_favorites_authenticated(self):
        """Test viewing favorites when authenticated"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Add a job to favorites
        self.applicant.favorites.add(self.job1)
        
        response = self.client.get(reverse('applicants-favourites'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_favourites.html')
        self.assertIn('favorite_jobs', response.context)
        self.assertEqual(len(response.context['favorite_jobs']), 1)
        self.assertIn(self.job1, response.context['favorite_jobs'])

    def test_view_favorites_unauthenticated(self):
        """Test viewing favorites when not logged in"""
        response = self.client.get(reverse('applicants-favourites'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, 
            f"{reverse('log_in')}?next={reverse('applicants-favourites')}"
        )

    def test_non_applicant_access(self):
        """Test that non-applicants cannot access favorites"""
        self.client.login(username='@testemployer', password='testpass123')
        response = self.client.get(reverse('applicants-favourites'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode(), "You are not authorized to view this page.")

    def test_toggle_favorite_add(self):
        """Test adding a job to favorites"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        response = self.client.post(
            reverse('toggle_favorite'),
            data=json.dumps({'job_id': self.job1.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['favorited'])
        self.assertTrue(self.job1 in self.applicant.favorites.all())

    def test_toggle_favorite_remove(self):
        """Test removing a job from favorites"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Add job to favorites first
        self.applicant.favorites.add(self.job1)
        
        response = self.client.post(
            reverse('toggle_favorite'),
            data=json.dumps({'job_id': self.job1.id}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['favorited'])
        self.assertFalse(self.job1 in self.applicant.favorites.all())

    def test_toggle_favorite_invalid_job(self):
        """Test toggling favorite with invalid job ID"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        response = self.client.post(
            reverse('toggle_favorite'),
            data=json.dumps({'job_id': 99999}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'Job not found')

    def test_multiple_favorites(self):
        """Test adding multiple jobs to favorites"""
        self.client.login(username='@testapplicant', password='testpass123')
        
        # Add both jobs to favorites
        self.applicant.favorites.add(self.job1, self.job2)
        
        response = self.client.get(reverse('applicants-favourites'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['favorite_jobs']), 2)
        self.assertIn(self.job1, response.context['favorite_jobs'])
        self.assertIn(self.job2, response.context['favorite_jobs']) 