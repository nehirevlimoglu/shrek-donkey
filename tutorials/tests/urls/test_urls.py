from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import admin

# Import your views so that you can compare the resolved view functions.
from tutorials.views.views import log_in, log_out, sign_up  
from tutorials.views.applicant_views import (
    applicants_home_page, applicants_account, applicants_applied_jobs, \
    applicants_favourites, applicants_notifications, applicants_edit_profile, \
    applicants_analytics, apply_for_job, job_detail, applicants_application
)
from tutorials.views.employer_views import applicant_profile, \
    employer_home_page, view_employer_analytics, employer_settings, change_password, \
    employer_job_listings, create_job_listings, job_detail_view, edit_job_view, \
    employer_calendar, employer_candidates, get_interviews, edit_company_profile, \
    delete_account, employer_notifications, get_employer_events, review_application, \
    mark_notification_as_read, schedule_interview, accept_candidate, reject_candidate

from tutorials.views.admin_views import (
    admin_home_page, admin_job_listings, admin_settings, admin_notifications, \
    review_job, update_job_status
)


class TestURLPatterns(TestCase):
    """Tests for all URL patterns defined in your urls file."""

    # Admin site URL
    def test_admin_index(self):
        url = reverse('admin:index')
        self.assertEqual(url, '/admin/')
        resolver = resolve('/admin/')
        self.assertTrue('admin' in resolver.func.__module__)

    # Home and Authentication
    def test_home(self):
        url = reverse('home')
        self.assertEqual(url, '/')
        resolver = resolve('/')
        self.assertEqual(resolver.func, log_in)

    def test_log_in(self):
        url = reverse('log-in')
        self.assertEqual(url, '/log_in/')
        resolver = resolve('/log_in/')
        self.assertEqual(resolver.func, log_in)

    def test_log_out(self):
        url = reverse('log-out')
        self.assertEqual(url, '/logout/')
        resolver = resolve('/logout/')
        self.assertEqual(resolver.func, log_out)

    # Applicants URLs
    def test_applicants_home_page(self):
        url = reverse('applicants-home-page')
        self.assertEqual(url, '/applicants_home_page/')
        resolver = resolve('/applicants_home_page/')
        self.assertEqual(resolver.func, applicants_home_page)

    def test_applicants_favourites(self):
        url = reverse('applicants-favourites')
        self.assertEqual(url, '/applicants_favourites/')
        resolver = resolve('/applicants_favourites/')
        self.assertEqual(resolver.func, applicants_favourites)

    def test_applicants_applied_jobs(self):
        url = reverse('applicants-applied-jobs')
        self.assertEqual(url, '/applicants_applied_jobs/')
        resolver = resolve('/applicants_applied_jobs/')
        self.assertEqual(resolver.func, applicants_applied_jobs)

    def test_applicants_account(self):
        url = reverse('applicants-account')
        self.assertEqual(url, '/applicants_account/')
        resolver = resolve('/applicants_account/')
        self.assertEqual(resolver.func, applicants_account)

    def test_applicants_notifications(self):
        url = reverse('applicants-notifications')
        self.assertEqual(url, '/applicants_notifications/')
        resolver = resolve('/applicants_notifications/')
        self.assertEqual(resolver.func, applicants_notifications)

    def test_applicants_edit_profile(self):
        url = reverse('applicants-edit-profile')
        self.assertEqual(url, '/applicants_edit_profile/')
        resolver = resolve('/applicants_edit_profile/')
        self.assertEqual(resolver.func, applicants_edit_profile)

    def test_applicants_analytics(self):
        url = reverse('applicants-analytics')
        self.assertEqual(url, '/applicants_analytics/')
        resolver = resolve('/applicants_analytics/')
        self.assertEqual(resolver.func, applicants_analytics)

    # Admin URLs
    def test_admin_home_page(self):
        url = reverse('admin_home_page')
        self.assertEqual(url, '/admin_home_page/')
        resolver = resolve('/admin_home_page/')
        self.assertEqual(resolver.func, admin_home_page)

    def test_admin_notifications(self):
        url = reverse('admin_notifications')
        self.assertEqual(url, '/admin_notifications/')
        resolver = resolve('/admin_notifications/')
        self.assertEqual(resolver.func, admin_notifications)

    def test_admin_job_listings(self):
        url = reverse('admin_job_listings')
        self.assertEqual(url, '/admin-job-listings/')
        resolver = resolve('/admin-job-listings/')
        self.assertEqual(resolver.func, admin_job_listings)

    def test_admin_settings(self):
        url = reverse('admin_settings')
        self.assertEqual(url, '/admin_settings/')
        resolver = resolve('/admin_settings/')
        self.assertEqual(resolver.func, admin_settings)

    def test_update_job_status(self):
        url = reverse('update_job_status')
        self.assertEqual(url, '/update-job-status/')
        resolver = resolve('/update-job-status/')
        self.assertEqual(resolver.func, update_job_status)

    # Employer URLs
    def test_employer_home_page(self):
        url = reverse('employer_home_page')
        self.assertEqual(url, '/employer_home_page/')
        resolver = resolve('/employer_home_page/')
        self.assertEqual(resolver.func, employer_home_page)

    def test_employer_job_listings(self):
        url = reverse('employer_job_listings')
        self.assertEqual(url, '/employer_job_listings/')
        resolver = resolve('/employer_job_listings/')
        self.assertEqual(resolver.func, employer_job_listings)

    def test_create_job_listings(self):
        url = reverse('create_job_listings')
        self.assertEqual(url, '/create_job_listings/')
        resolver = resolve('/create_job_listings/')
        self.assertEqual(resolver.func, create_job_listings)

    def test_employer_analytics(self):
        url = reverse('employer_analytics')
        self.assertEqual(url, '/employer_analytics/')
        resolver = resolve('/employer_analytics/')
        self.assertEqual(resolver.func, view_employer_analytics)

    def test_employer_job_detail(self):
        url = reverse('employer_job_detail', kwargs={'pk': 1})
        self.assertEqual(url, '/jobs/1/')
        resolver = resolve('/jobs/1/')
        self.assertEqual(resolver.func, job_detail_view)

    def test_job_edit(self):
        url = reverse('job_edit', kwargs={'pk': 1})
        self.assertEqual(url, '/jobs/1/edit/')
        resolver = resolve('/jobs/1/edit/')
        self.assertEqual(resolver.func, edit_job_view)

    def test_change_password(self):
        url = reverse('change_password')
        self.assertEqual(url, '/change-password/')
        resolver = resolve('/change-password/')
        self.assertEqual(resolver.func, change_password)

    def test_sign_up(self):
        url = reverse('sign-up')
        self.assertEqual(url, '/sign_up/')
        resolver = resolve('/sign_up/')
        self.assertEqual(resolver.func, sign_up)

    def test_employer_settings(self):
        url = reverse('employer_settings')
        self.assertEqual(url, '/employer_settings/')
        resolver = resolve('/employer_settings/')
        self.assertEqual(resolver.func, employer_settings)

    def test_employer_create_job_listing(self):
        url = reverse('employer_create_job_listing')
        self.assertEqual(url, '/create-job/')
        resolver = resolve('/create-job/')
        self.assertEqual(resolver.func, create_job_listings)

    def test_employer_candidates(self):
        url = reverse('employer_candidates')
        self.assertEqual(url, '/candidates/')
        resolver = resolve('/candidates/')
        self.assertEqual(resolver.func, employer_candidates)

    def test_employer_calendar(self):
        url = reverse('employer_calendar')
        self.assertEqual(url, '/interviews/')
        resolver = resolve('/interviews/')
        self.assertEqual(resolver.func, employer_calendar)

    def test_edit_company_profile(self):
        url = reverse('edit_company_profile')
        self.assertEqual(url, '/settings/edit_profile/')
        resolver = resolve('/settings/edit_profile/')
        self.assertEqual(resolver.func, edit_company_profile)

    def test_delete_account(self):
        url = reverse('delete_account')
        self.assertEqual(url, '/settings/delete_account/')
        resolver = resolve('/settings/delete_account/')
        self.assertEqual(resolver.func, delete_account)

    # Job URLs
    def test_job_detail(self):
        url = reverse('job_detail', kwargs={'job_id': 1})
        self.assertEqual(url, '/job/1/')
        resolver = resolve('/job/1/')
        # Since 'job_detail' is defined twice, the last one in the file takes precedence.
        # We allow either view here.
        self.assertIn(resolver.func, [job_detail, job_detail_view])

    def test_apply_for_job(self):
        url = reverse('apply_for_job', kwargs={'job_id': 1})
        self.assertEqual(url, '/job/1/apply/')
        resolver = resolve('/job/1/apply/')
        self.assertEqual(resolver.func, apply_for_job)

    def test_applicants_application(self):
        url = reverse('applicants_application', kwargs={'job_id': 1})
        self.assertEqual(url, '/applicants_application/1/')
        resolver = resolve('/applicants_application/1/')
        self.assertEqual(resolver.func, applicants_application)

    # Employer additional URLs
    def test_employer_notifications(self):
        url = reverse('employer_notifications')
        self.assertEqual(url, '/employer-notifications/')
        resolver = resolve('/employer-notifications/')
        self.assertEqual(resolver.func, employer_notifications)

    def test_get_employer_events(self):
        url = reverse('get_employer_events')
        self.assertEqual(url, '/get-employer-events/')
        resolver = resolve('/get-employer-events/')
        self.assertEqual(resolver.func, get_employer_events)

    def test_review_application(self):
        url = reverse('review_application', kwargs={'application_id': 1})
        self.assertEqual(url, '/review-application/1/')
        resolver = resolve('/review-application/1/')
        self.assertEqual(resolver.func, review_application)

    def test_mark_notification_as_read(self):
        url = reverse('mark_notification_as_read', kwargs={'notification_id': 1})
        self.assertEqual(url, '/mark-notification-read/1/')
        resolver = resolve('/mark-notification-read/1/')
        self.assertEqual(resolver.func, mark_notification_as_read)

    def test_applicant_profile(self):
        url = reverse('applicant_profile', kwargs={'applicant_id': 1})
        self.assertEqual(url, '/applicants/1/')
        resolver = resolve('/applicants/1/')
        self.assertEqual(resolver.func, applicant_profile)

    def test_schedule_interview(self):
        url = reverse('schedule_interview', kwargs={'applicant_id': 1})
        self.assertEqual(url, '/interviews/schedule/1/')
        resolver = resolve('/interviews/schedule/1/')
        self.assertEqual(resolver.func, schedule_interview)

    def test_get_interview_events(self):
        url = reverse('get_interview_events')
        self.assertEqual(url, '/get-interview-events/')
        resolver = resolve('/get-interview-events/')
        self.assertEqual(resolver.func, get_interviews)
