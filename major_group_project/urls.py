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
from tutorials.views.views import log_in, home_page, log_out  
from tutorials.views.admin_views import admin_home_page, admin_job_listings, admin_settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', log_in, name='home'),
    path('log_in/', log_in, name='log-in'),  
    path('homepage/', home_page, name='home-page'),
    path('logout/', log_out, name='log-out'),
    path('admin_home_page/', admin_home_page, name='admin_home_page'),
    path('admin_job_listings/', admin_job_listings, name='admin_job_listings'),
    path('admin_settings/', admin_settings, name='admin_settings')
]