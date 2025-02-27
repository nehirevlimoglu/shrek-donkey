from django.contrib import admin
from django.urls import path
from tutorials.views.views import log_in, log_out, sign_up  
from tutorials.views.applicant_views import applicants_home_page, applicants_account, applicants_applied_jobs, applicants_favourites, applicants_notifications, applicants_edit_profile, applicants_analytics
from tutorials.views.admin_views import admin_home_page, admin_job_listings, admin_settings, admin_notifications, review_job
from tutorials.views.employer_views import employer_home_page, view_employer_analytics, employer_settings, change_password, employer_job_listings, create_job_listings, job_detail_view, edit_job_view, employer_interviews, employer_candidates, get_interviews, edit_company_profile, delete_account

urlpatterns = [
    path('admin/', admin.site.urls),
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
    path('admin_notifications/', admin_notifications, name='admin_notifications'),
    path('admin-job-listings/', admin_job_listings, name='admin_job_listings'),
     path('admin_settings/', admin_settings, name='admin_settings'),

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
    path('interviews/', employer_interviews, name='employer_interviews'),
    path("settings/edit_profile/", edit_company_profile, name="edit_company_profile"),
    path("settings/delete_account/", delete_account, name="delete_account"),


]
