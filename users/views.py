from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required



def login(request):        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('users:login')

    return render(request, 'users/login.html')



@login_required(login_url='users:login')
def dashboard(request):
    return render(request, 'users/dashboard.html')