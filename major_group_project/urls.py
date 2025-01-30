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
from tutorials.views.views import log_in, home_page, log_out  # Import your views
from tutorials.views.applicant_views import applicants_home_page, applicants_account 
from tutorials.views.views import account, favourites, applied_jobs
urlpatterns =[
    path('admin/', admin.site.urls),
    path('log_in/', log_in, name='log-in'),  # ✅ Ensure this matches the form action
    path('homepage/', home_page, name='home-page'),
    path('logout/', log_out, name='log-out'),
    path('', home_page, name='home'),
    path('applicants_home_page/', applicants_home_page, name='applicants-home-page'), #m
    path('favourites/', favourites, name='favourites'),
    path('applied-jobs/', applied_jobs, name='applied-jobs'),
    path("applicants_account/", applicants_account, name="applicants-account"),
]

