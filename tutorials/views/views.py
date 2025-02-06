from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.helpers import login_prohibited
from tutorials.forms.forms import SignUpForm


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
            user = form.save()  # No more restriction
            login(request, user)
            if request.user.role == 'Admin':
                return redirect('admin_home_page')  
            elif request.user.role == 'Employer':
                return redirect('employer_home_page')  
            elif request.user.role == 'Applicant':
                return redirect('applicants_home_page')  
    else:
        form = SignUpForm()

    return render(request, 'sign_up.html', {'form': form})



def home_page(request):
    return render(request, 'home_page.html')

def log_out(request):
    print("User before logout:", request.user)  # ✅ Debug: Check user before logout
    logout(request)
<<<<<<< HEAD
    return redirect('log-in')  # Redirect to login page after logout

def account(request):
    return render(request, 'account.html')

def favourites(request):
    return render(request, 'favourites.html')

def applied_jobs(request):
    return render(request, 'applied_jobs.html')




=======
    print("User should be logged out now.")  # ✅ Debug: Confirm logout was called
    return redirect('log-in')  # ✅ Redirect to login page
>>>>>>> origin/employers
