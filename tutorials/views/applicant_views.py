from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

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