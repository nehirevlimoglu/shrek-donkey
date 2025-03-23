from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification
from tutorials.models.applicants_models import Applicant
from tutorials.models.employer_models import Employer

User = get_user_model()

class SubmitFeedbackViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.feedback_url = reverse('submit_feedback')

        self.applicant_user = User.objects.create_user(
            username='applicantuser',
            email='applicant@example.com',
            password='testpass',
            role='Applicant'
        )
        self.employer_user = User.objects.create_user(
            username='employeruser',
            email='employer@example.com',
            password='testpass',
            role='Employer'
        )

        Applicant.objects.create(user=self.applicant_user)
        Employer.objects.create(user=self.employer_user, company_name='TestCo')

    def test_applicant_can_submit_valid_feedback(self):
        self.client.login(username='applicantuser', password='testpass')

        response = self.client.post(self.feedback_url, {
            'feedback_type': 'suggestion',
            'subject': 'Improve UI',
            'message': 'Consider updating colors.',
            'priority': 'high'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you for your feedback!')
        self.assertEqual(Notification.objects.count(), 1)

        notification = Notification.objects.first()
        self.assertEqual(notification.title, 'New Feedback: Improve UI')
        self.assertEqual(notification.feedback_type, 'suggestion')
        self.assertEqual(notification.priority, 'high')
        self.assertEqual(notification.sender, self.applicant_user)
        self.assertEqual(notification.sender_type, 'applicant')

    def test_employer_can_submit_valid_feedback(self):
        self.client.login(username='employeruser', password='testpass')

        response = self.client.post(self.feedback_url, {
            'feedback_type': 'issue',
            'subject': 'Login Error',
            'message': 'Cannot log in from Safari browser.',
            'priority': 'medium'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thank you for your feedback!')
        self.assertEqual(Notification.objects.count(), 1)

        notification = Notification.objects.first()
        self.assertEqual(notification.title, 'New Feedback: Login Error')
        self.assertEqual(notification.feedback_type, 'issue')
        self.assertEqual(notification.priority, 'medium')
        self.assertEqual(notification.sender, self.employer_user)
        self.assertEqual(notification.sender_type, 'employer')

    def test_feedback_submission_missing_required_fields(self):
        self.client.login(username='applicantuser', password='testpass')

        response = self.client.post(self.feedback_url, {
            'feedback_type': '',  # Missing
            'subject': '',        # Missing
            'message': ''         # Missing
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'All required fields must be filled out.')
        self.assertEqual(Notification.objects.count(), 0)

    def test_feedback_requires_login(self):
        response = self.client.get(self.feedback_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/log_in/?next={self.feedback_url}')

    def test_feedback_database_exception_handled_gracefully(self):
        self.client.login(username='applicantuser', password='testpass')

        # Simulate database exception by mocking Notification.objects.create
        from unittest.mock import patch

        with patch('tutorials.models.admin_models.Notification.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database error")

            response = self.client.post(self.feedback_url, {
                'feedback_type': 'issue',
                'subject': 'Database issue',
                'message': 'Testing error handling.',
                'error_message': 'All required fields must be filled out.',
                'priority': 'medium'
            })

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Error submitting feedback: Database error')
            self.assertEqual(Notification.objects.count(), 0)
