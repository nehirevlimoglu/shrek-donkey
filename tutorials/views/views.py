from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.helpers import login_prohibited
from tutorials.forms.forms import SignUpForm
from django.http import HttpResponseRedirect
from django.urls import reverse



def log_in(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        print(f"Attempting login: {username} | {password}")  # ✅ Debugging step
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f"User authenticated: {user.username} | Role: {user.role}")  # ✅ Debugging step
            login(request, user)

            # ✅ Redirect based on role
            if request.user.role == 'Admin':
                return redirect('admin_home_page')  
            elif request.user.role == 'Employer':
                return redirect('employer_home_page')  
            elif request.user.role == 'Applicant':
                return redirect('applicants_home_page')  
            
            return redirect('home-page')  # Fallback

        else:
            print("Authentication failed")  # ❌ This means the username/password is incorrect.
    
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
                return HttpResponseRedirect(f"{reverse('applicants_home_page')}?newUser=true")
    else:
        form = SignUpForm()

    return render(request, 'sign_up.html', {'form': form})

def log_out(request):
<<<<<<< HEAD
    print("User before logout:", request.user)  # ✅ Debug: Check user before logout
    logout(request)
    return redirect('log-in')  # Redirect to login page after logout




    
=======
    print("User before logout:", request.user) 
    logout(request)  
    print("User after logout:", request.user)  
    return redirect('log-in')
>>>>>>> employers
