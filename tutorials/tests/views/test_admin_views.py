from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models.admin_models import Admin, Notification, NotificationPreference
from tutorials.models.user_model import User
from tutorials.models.employer_models import Job, Candidate, Employer
from django.utils import timezone
from datetime import timedelta
import json
from django.contrib.messages import get_messages

class AdminViewsTest(TestCase):
    """Test cases for admin views"""
    
    def setUp(self):
        """Set up test data for admin views tests"""
        # Create admin user
        self.admin_user = Admin.objects.create_user(
            username='testadmin',
            email='testadmin@example.com',
            password='password123',
            first_name='Test',
            last_name='Admin',
            role='Admin'
        )
        
        # Create employer user
        self.employer_user = Employer.objects.create_user(
            username='testemployer',
            email='employer@example.com',
            password='password123',
            role='Employer',
            company_name='Test Company',
            industry='Technology'
        )
        
        # Create job listings
        self.job1 = Job.objects.create(
            title='Test Job 1',
            company_name='Test Company',
            employer=self.employer_user,
            location='Test Location',
            job_type='Full-time',
            salary=50000,
            description='Test job description 1',
            requirements='Test job requirements 1',
            application_deadline=timezone.now() + timedelta(days=10)
        )
        
        self.job2 = Job.objects.create(
            title='Test Job 2',
            company_name='Test Company',
            employer=self.employer_user,
            location='Test Location',
            job_type='Part-time',
            salary=25000,
            description='Test job description 2',
            requirements='Test job requirements 2',
            application_deadline=timezone.now() - timedelta(days=5)  # Expired
        )
        
        # Create notifications
        self.notification1 = Notification.objects.create(
            recipient=self.admin_user,
            title='Test Notification 1',
            message='This is a test notification 1.',
            notification_type='job',
            priority='high',
            is_read=False
        )
        
        self.notification2 = Notification.objects.create(
            recipient=self.admin_user,
            title='Test Notification 2',
            message='This is a test notification 2.',
            notification_type='application',
            priority='medium',
            is_read=True
        )
        
        # Set up client
        self.client = Client()
        
        # Log in as admin
        self.client.login(username='testadmin', password='password123')
    
    def test_admin_home_page(self):
        """Test admin home page view"""
        response = self.client.get(reverse('admin_home_page'))
        
        # Check response status and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_home_page.html')
        
        # Check context data
        self.assertIn('total_job_listings', response.context)
        self.assertEqual(response.context['total_job_listings'], 2)
        self.assertIn('pending_applications', response.context)
        self.assertIn('total_active_users', response.context)
        self.assertIn('new_hires_this_month', response.context)
    
    def test_admin_job_listings(self):
        """Test admin job listings view"""
        response = self.client.get(reverse('admin_job_listings'))
        
        # Check response status and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_job_listings.html')
        
        # Check context data
        self.assertIn('jobs', response.context)
        self.assertEqual(len(response.context['jobs']), 2)
        self.assertIn('total_jobs', response.context)
        self.assertEqual(response.context['total_jobs'], 2)
        self.assertIn('open_jobs', response.context)
        self.assertIn('closed_jobs', response.context)
        
        # Test search functionality
        response = self.client.get(reverse('admin_job_listings') + '?search=Test Job 1')
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0].title, 'Test Job 1')
        
        # Test status filter
        response = self.client.get(reverse('admin_job_listings') + '?status=closed')
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0].title, 'Test Job 2')
        
        response = self.client.get(reverse('admin_job_listings') + '?status=open')
        self.assertEqual(len(response.context['jobs']), 1)
        self.assertEqual(response.context['jobs'][0].title, 'Test Job 1')
    
    def test_admin_job_detail(self):
        """Test admin job detail view"""
        response = self.client.get(reverse('admin_job_detail', args=[self.job1.id]))
        
        # Check response status and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_job_detail.html')
        
        # Check context data
        self.assertIn('job', response.context)
        self.assertEqual(response.context['job'], self.job1)
        self.assertIn('candidates', response.context)
        self.assertIn('employer', response.context)
        self.assertEqual(response.context['employer'], self.employer_user)
    
    def test_admin_edit_job(self):
        """Test admin edit job view"""
        # Test GET request
        response = self.client.get(reverse('admin_edit_job', args=[self.job1.id]))
        
        # Check response status and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_edit_job.html')
        
        # Check context data
        self.assertIn('job', response.context)
        self.assertEqual(response.context['job'], self.job1)
        
        # Test POST request
        response = self.client.post(
            reverse('admin_edit_job', args=[self.job1.id]),
            {
                'title': 'Updated Job Title',
                'company_name': 'Updated Company',
                'location': 'Updated Location',
                'job_type': 'Internship',
                'salary': '60000',
                'description': 'Updated description',
                'requirements': 'Updated requirements',
                'application_deadline': (timezone.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
                'contact_email': 'updated@example.com'
            }
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_job_detail', args=[self.job1.id]))
        
        # Refresh job from database
        self.job1.refresh_from_db()
        
        # Check updated values
        self.assertEqual(self.job1.title, 'Updated Job Title')
        self.assertEqual(self.job1.company_name, 'Updated Company')
        self.assertEqual(self.job1.location, 'Updated Location')
        self.assertEqual(self.job1.job_type, 'Internship')
        self.assertEqual(self.job1.salary, '60000')
        self.assertEqual(self.job1.description, 'Updated description')
        self.assertEqual(self.job1.requirements, 'Updated requirements')
        self.assertEqual(self.job1.contact_email, 'updated@example.com')
    
    def test_admin_delete_job(self):
        """Test admin delete job view"""
        response = self.client.post(
            reverse('admin_delete_job', args=[self.job1.id]),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        
        # Check job is deleted
        self.assertFalse(Job.objects.filter(id=self.job1.id).exists())
    
    def test_admin_toggle_job_status(self):
        """Test admin toggle job status view"""
        # Set up a job that is currently active
        job = self.job1
        job.is_active = True
        job.save()
        
        # Toggle job status (deactivate)
        response = self.client.post(
            reverse('admin_toggle_job_status', args=[job.id]),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['new_status'], False)
        
        # Refresh job from database
        job.refresh_from_db()
        self.assertFalse(job.is_active)
        
        # Toggle job status again (activate)
        response = self.client.post(
            reverse('admin_toggle_job_status', args=[job.id]),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['new_status'], True)
        
        # Refresh job from database
        job.refresh_from_db()
        self.assertTrue(job.is_active)
    
    def test_admin_settings(self):
        """Test admin settings view"""
        # Test GET request
        response = self.client.get(reverse('admin_settings'))
        
        # Check response status and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_settings.html')
        
        # Check context data
        self.assertIn('tab', response.context)
        self.assertEqual(response.context['tab'], 'profile')
        self.assertIn('admin', response.context)
        self.assertIn('user', response.context)
        
        # Test POST request for profile update
        response = self.client.post(
            reverse('admin_settings'),
            {
                'update_profile': True,
                'username': 'updatedadmin',
                'email': 'updated@example.com',
                'first_name': 'Updated',
                'last_name': 'Admin',
                'phone_number': '+9876543210'
            }
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_settings'))
        
        # Refresh admin from database
        self.admin_user.refresh_from_db()
        
        # Check updated values
        self.assertEqual(self.admin_user.username, 'updatedadmin')
        self.assertEqual(self.admin_user.email, 'updated@example.com')
        self.assertEqual(self.admin_user.first_name, 'Updated')
        self.assertEqual(self.admin_user.last_name, 'Admin')
        self.assertEqual(self.admin_user.phone_number, '+9876543210')
        
        # Test POST request for password change
        response = self.client.post(
            reverse('admin_settings'),
            {
                'change_password': True,
                'current_password': 'password123',
                'new_password': 'newpassword123',
                'confirm_password': 'newpassword123'
            }
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_settings'))
        
        # Refresh admin from database
        self.admin_user.refresh_from_db()
        
        # Check password is updated
        self.assertTrue(self.admin_user.check_password('newpassword123'))
        
        # Test POST request for notification preferences update
        response = self.client.post(
            reverse('admin_settings'),
            {
                'update_notification_prefs': True,
                'job_notifications': 'on',
                'application_notifications': 'on',
                'email_delivery': 'on'
            }
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_settings'))
        
        # Check notification preferences are created
        notification_prefs = NotificationPreference.objects.get(admin=self.admin_user)
        self.assertTrue(notification_prefs.job_notifications)
        self.assertTrue(notification_prefs.application_notifications)
        self.assertFalse(notification_prefs.user_notifications)
        self.assertFalse(notification_prefs.system_notifications)
        self.assertTrue(notification_prefs.email_delivery)
        self.assertFalse(notification_prefs.dashboard_delivery)
    
    def test_admin_notifications(self):
        """Test admin notifications view"""
        response = self.client.get(reverse('admin_notifications'))
        
        # Check response status and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_notifications.html')
        
        # Check context data
        self.assertIn('notifications', response.context)
        self.assertEqual(len(response.context['notifications']), 2)
        self.assertIn('unread_count', response.context)
        self.assertEqual(response.context['unread_count'], 1)
        
        # Test filter by read status
        response = self.client.get(reverse('admin_notifications') + '?is_read=unread')
        self.assertEqual(len(response.context['notifications']), 1)
        self.assertEqual(response.context['notifications'][0], self.notification1)
        
        response = self.client.get(reverse('admin_notifications') + '?is_read=read')
        self.assertEqual(len(response.context['notifications']), 1)
        self.assertEqual(response.context['notifications'][0], self.notification2)
        
        # Test filter by type
        response = self.client.get(reverse('admin_notifications') + '?type=job')
        self.assertEqual(len(response.context['notifications']), 1)
        self.assertEqual(response.context['notifications'][0], self.notification1)
        
        response = self.client.get(reverse('admin_notifications') + '?type=application')
        self.assertEqual(len(response.context['notifications']), 1)
        self.assertEqual(response.context['notifications'][0], self.notification2)
    
    def test_mark_notification_as_read(self):
        """Test marking notification as read"""
        response = self.client.post(reverse('mark_notification_as_read', args=[self.notification1.id]))
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Refresh notification from database
        self.notification1.refresh_from_db()
        
        # Check notification is marked as read
        self.assertTrue(self.notification1.is_read)
    
    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read"""
        response = self.client.post(reverse('mark_all_notifications_as_read'))
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Refresh notifications from database
        self.notification1.refresh_from_db()
        self.notification2.refresh_from_db()
        
        # Check all notifications are marked as read
        self.assertTrue(self.notification1.is_read)
        self.assertTrue(self.notification2.is_read)
    
    def test_delete_notification(self):
        """Test deleting a notification"""
        response = self.client.post(reverse('delete_notification', args=[self.notification1.id]))
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Refresh notification from database
        self.notification1.refresh_from_db()
        
        # Check notification is soft deleted
        self.assertTrue(self.notification1.is_deleted)
    
    def test_delete_all_notifications(self):
        """Test deleting all notifications"""
        response = self.client.post(reverse('delete_all_notifications'))
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        
        # Refresh notifications from database
        self.notification1.refresh_from_db()
        self.notification2.refresh_from_db()
        
        # Check all notifications are soft deleted
        self.assertTrue(self.notification1.is_deleted)
        self.assertTrue(self.notification2.is_deleted)
    
    def test_generate_admin_notification(self):
        """Test generating admin notification"""
        # Count notifications before
        count_before = Notification.objects.count()
        
        response = self.client.get(reverse('admin_notifications_generate'))
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_notifications'))
        
        # Count notifications after
        count_after = Notification.objects.count()
        
        # Check new notification is created
        self.assertEqual(count_after, count_before + 1)
    
    def test_generate_test_notifications(self):
        """Test generating test notifications"""
        # Count notifications before
        count_before = Notification.objects.count()
        
        response = self.client.get(reverse('admin_notifications_generate_test'))
        
        # Check redirect
        self.assertRedirects(response, reverse('admin_notifications'))
        
        # Count notifications after
        count_after = Notification.objects.count()
        
        # Check multiple new notifications are created
        self.assertGreater(count_after, count_before)
    
    def test_admin_applications_view(self):
        """Test admin applications view"""
        # Create some candidate applications
        candidate1 = Candidate.objects.create(
            job=self.job1,
            first_name='Candidate',
            last_name='One',
            email='candidate1@example.com',
            resume='resumes/candidate1.pdf',
            application_status='Pending'
        )
        
        candidate2 = Candidate.objects.create(
            job=self.job1,
            first_name='Candidate',
            last_name='Two',
            email='candidate2@example.com',
            resume='resumes/candidate2.pdf',
            application_status='Interview'
        )
        
        response = self.client.get(reverse('admin_applications_view'))
        
        # Check response status and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_applications_view.html')
        
        # Check context data
        self.assertIn('applications', response.context)
        self.assertEqual(len(response.context['applications']), 2)
        self.assertIn('total_applications', response.context)
        self.assertEqual(response.context['total_applications'], 2)
        
        # Test search functionality
        response = self.client.get(reverse('admin_applications_view') + '?search=One')
        self.assertEqual(len(response.context['applications']), 1)
        
        # Test status filter
        response = self.client.get(reverse('admin_applications_view') + '?status=Pending')
        self.assertEqual(len(response.context['applications']), 1)
        
        response = self.client.get(reverse('admin_applications_view') + '?status=Interview')
        self.assertEqual(len(response.context['applications']), 1)
    
    def test_get_candidate_info(self):
        """Test getting candidate info"""
        # Create a candidate
        candidate = Candidate.objects.create(
            job=self.job1,
            first_name='Test',
            last_name='Candidate',
            email='testcandidate@example.com',
            resume='resumes/test.pdf',
            application_status='Pending'
        )
        
        response = self.client.get(reverse('get_candidate_info', args=[candidate.id]))
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check response data
        data = json.loads(response.content)
        self.assertEqual(data['id'], candidate.id)
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'Candidate')
        self.assertEqual(data['email'], 'testcandidate@example.com')
        self.assertEqual(data['status'], 'Pending')
    
    def test_update_candidate_status(self):
        """Test updating candidate status"""
        # Create a candidate
        candidate = Candidate.objects.create(
            job=self.job1,
            first_name='Test',
            last_name='Candidate',
            email='testcandidate@example.com',
            resume='resumes/test.pdf',
            application_status='Pending'
        )
        
        response = self.client.post(
            reverse('update_candidate_status', args=[candidate.id]),
            {'status': 'Interview'}
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check response data
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        
        # Refresh candidate from database
        candidate.refresh_from_db()
        
        # Check status is updated
        self.assertEqual(candidate.application_status, 'Interview')
    
    def test_non_admin_access(self):
        """Test that non-admin users cannot access admin views"""
        # Create a non-admin user
        non_admin = User.objects.create_user(
            username='nonadmin',
            email='nonadmin@example.com',
            password='password123',
            role='Applicant'
        )
        
        # Log in as non-admin
        self.client.login(username='nonadmin', password='password123')
        
        # Try to access admin home page
        response = self.client.get(reverse('admin_home_page'))
        
        # Should be redirected to login page or get a 404
        self.assertNotEqual(response.status_code, 200)
    
    def test_resolve_feedback(self):
        """Test resolving feedback"""
        # Create a feedback notification
        feedback = Notification.objects.create(
            recipient=self.admin_user,
            title='Feedback',
            message='This is a feedback message.',
            notification_type='feedback',
            feedback_type='suggestion',
            sender_type='applicant',
            is_read=False
        )
        
        response = self.client.post(
            reverse('resolve_feedback', args=[feedback.id]),
            {'resolution': 'This feedback has been resolved.'},
            content_type='application/json'
        )
        
        # Check response status
        self.assertEqual(response.status_code, 200)
        
        # Check response data
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        
        # Refresh feedback from database
        feedback.refresh_from_db()
        
        # Check feedback is marked as read
        self.assertTrue(feedback.is_read) 