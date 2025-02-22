"""
URL configuration for major_group_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
<<<<<<< HEAD
from tutorials.views.views import log_in, home_page, log_out  # Import your views
from tutorials.views.applicant_views import applicants_home_page, applicants_account, applicants_applied_jobs, applicants_favourites 
from tutorials.views.views import log_in, home_page, log_out, sign_up  
=======
from tutorials.views.views import log_in, log_out, sign_up  
>>>>>>> employers
from tutorials.views.admin_views import admin_home_page, admin_job_listings, admin_settings
from tutorials.views.employer_views import employer_home_page, view_employer_analytics, employer_settings,change_password, employer_settings, employer_job_listings, create_job_listings, job_detail_view, edit_job_view, employer_interviews, employer_candidates, get_interviews, edit_company_profile, delete_account



urlpatterns =[
    path('admin/', admin.site.urls),
    path('', log_in, name='home'),
    path('log_in/', log_in, name='log-in'),  
    path('logout/', log_out, name='log-out'),
    path('applicants_home_page/', applicants_home_page, name='applicants-home-page'), #m
    path('applicants_favourites/', applicants_favourites, name='applicants-favourites'),
    path('applicants-applied-jobs/', applicants_applied_jobs, name='applicants-applied-jobs'),
    path("applicants_account/", applicants_account, name="applicants-account"),
    path('admin_home_page/', admin_home_page, name='admin_home_page'),
    path('admin_job_listings', admin_job_listings, name='admin_job_listings'),
    path('employer_home_page', employer_home_page, name='employer_home_page'),
    path('employer_job_listings', employer_job_listings, name='employer_job_listings'),
    path('create_job_listings', create_job_listings, name='create_job_listings'),
    path('employer_analytics', view_employer_analytics, name='employer_analytics'),
    path('jobs/<int:pk>/', job_detail_view, name='employer_job_detail'),
    path('jobs/<int:pk>/edit/', edit_job_view, name='job_edit'),
    path('change-password/', change_password, name='change_password'),
    path('admin_job_listings/', admin_job_listings, name='admin_job_listings'),
    path('admin_settings/', admin_settings, name='admin_settings'),
    path('sign_up', sign_up, name='sign-up'),
    path('employer_settings/', employer_settings, name='employer_settings'),
    path('create-job/', create_job_listings, name='employer_create_job_listing'),
    path('candidates/', employer_candidates, name='employer_candidates'),
    path('interviews/', employer_interviews, name='employer_interviews'),
    path("settings/edit_profile/", edit_company_profile, name="edit_company_profile"),
    path("settings/delete_account/", delete_account, name="delete_account"),



]

