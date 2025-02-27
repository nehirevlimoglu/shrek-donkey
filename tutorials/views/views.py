from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.helpers import login_prohibited
from tutorials.forms.forms import SignUpForm
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse

def log_in(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Simplified role checking
            if user.role == 'Admin':
                return redirect('admin_home_page')  
            elif user.role == 'Employer':
                return redirect('employer_home_page')  
            else:  # Default to applicant page if not admin/employer
                return redirect('applicants-home-page')  

        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'log_in.html')


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user
            login(request, user)  # Log in the user

            # Redirect with URL parameter
            if request.user.role == 'Admin':
                return redirect('admin_home_page')
            elif request.user.role == 'Employer':
                return HttpResponseRedirect(f"{reverse('employer_home_page')}?newUser=true")
            elif request.user.role == 'Applicant':
                return HttpResponseRedirect(f"{reverse('applicants-home-page')}?newUser=true")
    else:
        form = SignUpForm()

    return render(request, 'sign_up.html', {'form': form})

def log_out(request):
    print("User before logout:", request.user)  # ✅ Debug: Check user before logout
    logout(request)
    return redirect('log-in')  # Redirect to login page after logout




    
