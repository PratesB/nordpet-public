from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import User



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



def logout(request):
    auth_logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('users:login')



@login_required(login_url='users:login')
def register_team(request):
    if request.user.role != 'ADM':
        return redirect('users:dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('users:register_team')
        
        photo = request.FILES.get('photo')

        user = User.objects.create_user(
            first_name=first_name, 
            last_name=last_name, 
            role=role, 
            phone=phone, 
            email=email, 
            password=password,
            photo=photo
        )
        messages.success(request, 'User created successfully')
        return redirect('users:team')

    return render(request, 'users/register_team.html')



from django.db.models import Q

@login_required(login_url='users:login')
def team(request):
    if request.user.role != 'ADM':
        return redirect('users:dashboard')
    
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    user_list = User.objects.all().order_by('-created_at')
    
    if search_query:
        user_list = user_list.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
        
    if role_filter:
        user_list = user_list.filter(role=role_filter)
    paginator = Paginator(user_list, 10) # 10 members per page
    
    page_number = request.GET.get('page')
    members = paginator.get_page(page_number)
    
    return render(request, 'users/team.html', {'members': members})