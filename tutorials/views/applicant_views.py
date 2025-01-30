from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.models.applicants_models import Applicant 
from tutorials.forms.applicants_forms import ApplicantForm 


def job_recommendations(request):
    jobs = [
        {"title": "Software Engineer", "company": "TechCorp", "location": "San Francisco, CA", "salary": "$120,000/year"},
        {"title": "Marketing Manager", "company": "MarketPros", "location": "New York, NY", "salary": "$90,000/year"},
        {"title": "Data Analyst", "company": "DataVision", "location": "Austin, TX", "salary": "$85,000/year"}
    ]
    return render(request, 'job_recommendations.html', {'jobs': jobs})

def applicants_home_page(request):
    return render(request, 'applicants_home_page.html')

def log_in(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('applicants_home_page')
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'log_in.html')

def log_out(request):
    logout(request)
    return redirect('log-in')



def applicants_account(request, applicant_id=None):
    """ Display and update the applicant's profile. """
    
    # If applicant_id is provided, fetch the specific applicant; otherwise, default to the first one (if needed)
    if applicant_id:
        applicant = get_object_or_404(Applicant, id=applicant_id)
    else:
        # Try to get the first applicant associated with the logged-in user (optional logic)
        applicant = Applicant.objects.first()

    if request.method == "POST":
        form = ApplicantForm(request.POST, request.FILES, instance=applicant)
        if form.is_valid():
            form.save()
            messages.success(request, "Your account has been updated successfully!")
            return redirect('applicants-account')  # Redirect to the same page to see updated info
        else:
            messages.error(request, "There was an error saving your account information.")
    else:
        form = ApplicantForm(instance=applicant)

    return render(request, "applicants_account.html", {"form": form, "applicant": applicant})


