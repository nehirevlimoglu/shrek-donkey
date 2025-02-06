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
=======
from tutorials.views.views import log_in, home_page, log_out, sign_up  
from tutorials.views.admin_views import admin_home_page, admin_job_listings, admin_settings
from tutorials.views.employer_views import employer_home_page, view_listings, view_reports, view_settings, create_job_listing


>>>>>>> origin/employers

urlpatterns =[
    path('admin/', admin.site.urls),
    path('', log_in, name='home'),
    path('log_in/', log_in, name='log-in'),  
    path('homepage/', home_page, name='home-page'),
    path('logout/', log_out, name='log-out'),
<<<<<<< HEAD
    path('applicants_home_page/', applicants_home_page, name='applicants-home-page'), #m
    path('applicants_favourites/', applicants_favourites, name='applicants-favourites'),
    path('applicants-applied-jobs/', applicants_applied_jobs, name='applicants-applied-jobs'),
    path("applicants_account/", applicants_account, name="applicants-account"),
=======
    path('admin_home_page/', admin_home_page, name='admin_home_page'),
    path('admin_job_listings', admin_job_listings, name='admin_job_listings'),

    path('employer_home_page', employer_home_page, name='employer_home_page'),
    path('employer_job_listings', view_listings, name='employer_job_listings'),
    path('employer_reports', view_reports, name='employer_reports'),
    path('employer_settings', view_settings, name='employer_settings'),
    path('employer_create_job_listings', create_job_listing, name='employer_create_job_listing'),

    path('admin_job_listings/', admin_job_listings, name='admin_job_listings'),
    path('admin_settings/', admin_settings, name='admin_settings'),
    path('sign_up', sign_up, name='sign-up'),
>>>>>>> origin/employers
]

