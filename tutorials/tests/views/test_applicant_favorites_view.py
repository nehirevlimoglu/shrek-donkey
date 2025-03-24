from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.applicants_models import Applicant
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render



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
        
        # Set up test client
        self.client = Client()

    def test_view_favorites_authenticated(self):
        """Test viewing favorites when authenticated"""
        self.client.login(username='@testapplicant', password='testpass123')
        response = self.client.get(reverse('applicants-favourites'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_favourites.html')

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
        # Create and login as non-applicant user
        non_applicant = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            role='Employer'
        )
        self.client.login(username='@testemployer', password='testpass123')
        
        response = self.client.get(reverse('applicants-favourites'))
        self.assertEqual(response.status_code, 403) 