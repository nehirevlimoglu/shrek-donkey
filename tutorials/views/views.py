from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def log_in(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home-page')  # Redirect to homepage after login
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'log_in.html')

def home_page(request):
    return render(request, 'home_page.html')

def log_out(request):
    logout(request)
    return redirect('log-in')  # Redirect to login page after logout
