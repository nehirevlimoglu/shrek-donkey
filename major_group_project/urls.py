from django.contrib import admin
from django.urls import path, include
from tutorials.views.applicant_views import applicants_home_page, applicants_account, applicants_applied_jobs, applicants_favourites 
from tutorials.views.views import log_in, log_out, sign_up  
from tutorials.views.admin_views import admin_home_page, admin_job_listings, admin_settings, get_active_users_data, admin_job_detail, admin_edit_job, admin_delete_job, admin_toggle_job_status, admin_applications_view
from tutorials.views.employer_views import employer_home_page, view_employer_analytics, employer_settings,change_password, employer_settings, employer_job_listings, create_job_listings, job_detail_view, edit_job_view,  employer_candidates, get_interviews, edit_company_profile, delete_account, schedule_interview, interview_detail, reschedule_interview


from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from tutorials.views.views import log_in, log_out, sign_up  

from tutorials.views.admin_views import admin_home_page, admin_job_listings, admin_settings, admin_notifications, admin_applications_view, admin_notifications_count, generate_admin_notification, mark_notification_as_read, mark_all_notifications_as_read, delete_notification, delete_all_notifications


from tutorials.views.applicant_views import applicants_home_page, applicants_account, applicants_applied_jobs, applicants_favourites, applicants_notifications, applicants_edit_profile, applicants_analytics, apply_for_job, job_detail, applicants_application
from tutorials.views.employer_views import employer_home_page, view_employer_analytics, employer_settings, change_password, employer_job_listings, create_job_listings, job_detail_view, edit_job_view, employer_calendar, employer_candidates, get_interviews, edit_company_profile, delete_account, employer_notifications, get_employer_events, review_application, mark_notification_as_read, applicant_profile, schedule_interview, accept_candidate, reject_candidate

from tutorials.views.employer_views import job_detail_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('schedule/', include('schedule.urls')),
    path('', log_in, name='home'),
    path('log_in/', log_in, name='log-in'),  
    path('logout/', log_out, name='log-out'),

    path('applicants_home_page/', applicants_home_page, name='applicants-home-page'),
    path('applicants_favourites/', applicants_favourites, name='applicants-favourites'),
    path('applicants_applied_jobs/', applicants_applied_jobs, name='applicants-applied-jobs'),
    path("applicants_account/", applicants_account, name="applicants-account"),
    path('applicants_notifications/', applicants_notifications, name='applicants-notifications'),
    path('applicants_edit_profile/', applicants_edit_profile, name='applicants-edit-profile'),
    path('applicants_analytics/', applicants_analytics, name='applicants-analytics'),

    path('admin_home_page/', admin_home_page, name='admin_home_page'),
    path('admin_job_listings', admin_job_listings, name='admin_job_listings'),
    path('admin_notifications/', admin_notifications, name='admin_notifications'),
    path('admin_notifications/count/', admin_notifications_count, name='admin_notifications_count'),
    path('admin_notifications/generate/', generate_admin_notification, name='admin_notifications_generate'),
    path('admin_notifications/mark_read/<int:notification_id>/', mark_notification_as_read, name='mark_notification_as_read'),
    path('admin_notifications/mark_all_read/', mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('admin_notifications/delete/<int:notification_id>/', delete_notification, name='delete_notification'),
    path('admin_notifications/delete_all/', delete_all_notifications, name='delete_all_notifications'),
    path('admin_applications_view/', admin_applications_view, name='admin_applications_view'),
    path('admin_job_listings/', admin_job_listings, name='admin_job_listings'),
    path('admin_job_detail/<int:job_id>/', admin_job_detail, name='admin_job_detail'),
    path('admin_edit_job/<int:job_id>/', admin_edit_job, name='admin_edit_job'),
    path('admin_delete_job/<int:job_id>/', admin_delete_job, name='admin_delete_job'),
    path('admin_toggle_job_status/<int:job_id>/', admin_toggle_job_status, name='admin_toggle_job_status'),
    path('admin_settings/', admin_settings, name='admin_settings'),
    path('api/get_active_users_data/', get_active_users_data, name='get_active_users_data'),


    path('employer_home_page/', employer_home_page, name='employer_home_page'),
    path('employer_job_listings/', employer_job_listings, name='employer_job_listings'),
    path('create_job_listings/', create_job_listings, name='create_job_listings'),
    path('employer_analytics/', view_employer_analytics, name='employer_analytics'),
    path('jobs/<int:pk>/', job_detail_view, name='employer_job_detail'),
    path('jobs/<int:pk>/edit/', edit_job_view, name='job_edit'),
    path('change-password/', change_password, name='change_password'),
    path('sign_up/', sign_up, name='sign-up'),
    path('employer_settings/', employer_settings, name='employer_settings'),
    path('create-job/', create_job_listings, name='employer_create_job_listing'),
    path('candidates/', employer_candidates, name='employer_candidates'),
    path('interviews/', employer_calendar, name='employer_calendar'),
    path("settings/edit_profile/", edit_company_profile, name="edit_company_profile"),
    path("settings/delete_account/", delete_account, name="delete_account"),
    path('job/<int:job_id>/', job_detail_view, name='job_detail'),
    
    path('employer-notifications/', employer_notifications, name='employer_notifications'),
    path('get-employer-events/', get_employer_events, name='get_employer_events'),
    path('review-application/<int:application_id>/', review_application, name='review_application'),
    path('mark-notification-read/<int:notification_id>/', mark_notification_as_read, name='mark_notification_as_read'),
    path('applicants/<int:applicant_id>/', applicant_profile, name='applicant_profile'),
    path('interviews/schedule/<int:applicant_id>/', schedule_interview, name='schedule_interview'),
    path('get-interview-events/', get_interviews, name='get_interview_events'),

    path('job/<int:job_id>/apply/', apply_for_job, name='apply_for_job'),
    path("candidates/<int:candidate_id>/accept/", accept_candidate, name="accept_candidate"),
    path("candidates/<int:candidate_id>/reject/", reject_candidate, name="reject_candidate"),

    path('job/<int:job_id>/', job_detail, name='job_detail'),
    path('job/<int:job_id>/apply/', apply_for_job, name='apply_for_job'),
    path('applicants_application/<int:job_id>/', applicants_application, name='applicants_application'),


]


# ✅ Add this to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)