from django.contrib import admin
from django.urls import path
from tutorials.views.views import log_in, home_page, log_out  # Import your views
from tutorials.views.applicant_views import applicants_home_page 
from tutorials.views.applicant_views import applicants_account

urlpatterns = [
    path('admin/', admin.site.urls),
    path('log_in/', log_in, name='log-in'),  # ✅ Ensure this matches the form action
    path('homepage/', home_page, name='home-page'),
    path('logout/', log_out, name='log-out'),
    path('', home_page, name='home'),
    path('applicants_home_page/', applicants_home_page, name='applicants-home-page'),
    path('account/', applicants_account, name='applicants_account'),
]

