from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def admin_home_page(request):
    return render(request, 'admin_home_page.html')