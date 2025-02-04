from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from tutorials.helpers import login_prohibited


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



def home_page(request):
    return render(request, 'home_page.html')

def log_out(request):
    print("User before logout:", request.user)  # ✅ Debug: Check user before logout
    logout(request)
    print("User should be logged out now.")  # ✅ Debug: Confirm logout was called
    return redirect('log-in')  # ✅ Redirect to login page