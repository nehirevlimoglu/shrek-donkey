from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer, Job, Candidate, EmployerNotification
from tutorials.forms.forms import SignUpForm
from django.contrib.messages import get_messages
from tutorials.forms.employer_forms import CustomPasswordChangeForm
from django.contrib.auth.forms import PasswordChangeForm

User = get_user_model()

class EmployerHomePageViewTests(TestCase):
    """Test suite for employer home page view"""

    def setUp(self):
        """Set up test data for employer home page view"""
        # Create employer user first
        self.employer_user = User.objects.create_user(
            username="test_employer",
            password="password123",
            email="employer@example.com",
            role='Employer'  # Make sure to set the role
        )

        # Create test employer with user association
        self.employer = Employer.objects.create(
            user=self.employer_user,  # Link to user
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="New York",
            industry="Tech"
        )

        # Create test jobs - one active, one expired
        self.active_job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
<<<<<<< HEAD
            description="Looking for a great developer!",
            application_deadline=now().date() + timedelta(days=10)
        )
        
=======
            application_deadline=now().date() + timedelta(days=10),
            description="Looking for a great developer!",
            status="approved"  # <-- Add this line
        )

>>>>>>> main-at-commit2
        self.expired_job = Job.objects.create(
            employer=self.employer,
            title="Expired Job",
            description="This job is expired.",
            application_deadline=now().date() - timedelta(days=1)
        )

        # Create test applicant and candidate
        self.applicant_user = User.objects.create_user(
            username="test_applicant",
            password="password123",
            email="applicant@test.com",
            role='Applicant'  # Set appropriate role
        )
        
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.active_job,
            application_date=now(),
            first_name="John",
            last_name="Doe"
        )

        # Create test notification
        self.notification = EmployerNotification.objects.create(
            employer=self.employer,
            title="New Application",
            message="An applicant applied."
        )

        self.client = Client()

    def test_employer_not_found(self):
        """Test handling of non-existent employer profile"""
        # Create a user without an employer profile
        non_employer_user = User.objects.create_user(
            username='temp',
            password='temp123',
            email='temp@test.com'
        )
        self.client.force_login(non_employer_user)
        response = self.client.get(reverse("employer_home_page"))
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {"success": False, "error": "Employer profile not found"}
        )

    def test_successful_dashboard_load(self):
        """Test successful loading of employer dashboard with correct data"""
        self.client.force_login(self.employer_user)
        response = self.client.get(reverse("employer_home_page"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employers_home_page.html")

        # Test context data
        self.assertEqual(response.context["total_jobs"], 2)  # Total jobs (active + expired)
        self.assertEqual(response.context["active_listings"], 1)  # Only active jobs
        self.assertEqual(response.context["total_applicants"], 1)  # One candidate
        
        # Test recent applicants
        self.assertEqual(len(response.context["recent_applicants"]), 1)
        recent_applicant = response.context["recent_applicants"][0]
        self.assertEqual(recent_applicant.user.username, "test_applicant")
        self.assertEqual(recent_applicant.job, self.active_job)

        # Test notifications
        self.assertEqual(len(response.context["notifications"]), 1)
        notification = response.context["notifications"][0]
        self.assertEqual(notification.title, "New Application")
        self.assertEqual(notification.employer, self.employer)

    def test_empty_dashboard(self):
        """Test dashboard display when employer has no jobs, applicants, or notifications"""
        # Create new employer user and profile
        empty_employer_user = User.objects.create_user(
            username="empty_employer",
            password="password123",
            email="empty@example.com",
            role='Employer'
        )
        
        empty_employer = Employer.objects.create(
            user=empty_employer_user,
            username="empty_employer",
            email="empty@example.com",
            company_name="Empty Corp"
        )
        
        self.client.force_login(empty_employer_user)
        response = self.client.get(reverse("employer_home_page"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_jobs"], 0)
        self.assertEqual(response.context["active_listings"], 0)
        self.assertEqual(response.context["total_applicants"], 0)
        self.assertEqual(len(response.context["recent_applicants"]), 0)
        self.assertEqual(len(response.context["notifications"]), 0)

    def test_change_password(self):
        """Test password change functionality"""
        self.client.force_login(self.employer_user)
        
        # Test GET request
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'change_password.html')
        
        # Check for Django's built-in PasswordChangeForm instead
        self.assertTrue(isinstance(response.context['form'], PasswordChangeForm))
        
        # Test successful password change
        data = {
            'old_password': 'password123',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        }
        response = self.client.post(reverse('change_password'), data, follow=True)
        
        # Check redirect and success message
        self.assertRedirects(response, reverse('employer_settings'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Your password has been successfully changed.")
        
        # Verify password was actually changed
        self.employer_user.refresh_from_db()
        self.assertTrue(self.employer_user.check_password('newpassword123'))

    def test_change_password_invalid(self):
        """Test password change with invalid data"""
        self.client.force_login(self.employer_user)
        
        # Test with incorrect old password
        data = {
            'old_password': 'wrongpassword',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        }
        response = self.client.post(reverse('change_password'), data)
        
        # Check form is invalid
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'change_password.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "There was an issue with your password change. Please check and try again.")
        
        # Verify password was not changed
        self.employer_user.refresh_from_db()
        self.assertTrue(self.employer_user.check_password('password123'))

    def test_change_password_unauthenticated(self):
        """Test password change when user is not logged in"""
        self.client.logout()
        response = self.client.get(reverse('change_password'))
        self.assertRedirects(
            response, 
            f"{reverse('log_in')}?next={reverse('change_password')}"
        )


