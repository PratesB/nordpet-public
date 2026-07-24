from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages



def login(request):        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            return HttpResponse('User logged successfully!')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('users:login')

    return render(request, 'users/login.html')