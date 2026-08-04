from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import User
from clients.models import Appointment



def login(request):
    if request.user.is_authenticated:
        return redirect('users:dashboard')
                
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
    today = timezone.now().date()
    all_appointments = Appointment.objects.filter(scheduled_at__date=today).order_by('scheduled_at')
    
    today_appointments = []
    emergency_appointments = []
    urgent_triages = []
    
    red_count = 0
    orange_count = 0
    yellow_count = 0
    green_count = 0
    awaiting_triage = 0
    
    for appt in all_appointments:
        if appt.scheduled_at:
            appt.end_time = appt.scheduled_at + timedelta(minutes=appt.duration)
        else:
            appt.end_time = None
            
        triage = appt.animal.triage_set.filter(created_at__date=today).first()
        if triage:
            appt.triage_today = True
            appt.triage_risk_level = triage.risk_level
            
            if request.user.role == 'VET' and appt.veterinarian == request.user and appt.status not in ['completed', 'canceled']:
                triage.appt_status = appt.status
                urgent_triages.append(triage)
                
            if triage.risk_level == 'red':
                red_count += 1
            elif triage.risk_level == 'orange':
                orange_count += 1
            elif triage.risk_level == 'yellow':
                yellow_count += 1
            elif triage.risk_level == 'green':
                green_count += 1
        else:
            appt.triage_today = False
            appt.triage_risk_level = None
            if appt.status not in ['completed', 'canceled']:
                awaiting_triage += 1
            
        if appt.reason == 'emergency':
            if appt.status not in ['completed', 'canceled']:
                emergency_appointments.append(appt)
        else:
            if appt.status not in ['completed', 'canceled']:
                if request.user.role == 'VET':
                    if appt.veterinarian == request.user and not triage:
                        today_appointments.append(appt)
                else:
                    today_appointments.append(appt)
            
    completed_appts = all_appointments.filter(status='completed').count()
    canceled_appts = all_appointments.filter(status='canceled').count()
    total_emergencies = all_appointments.filter(reason='emergency').count()
    scheduled_appts = all_appointments.filter(status='scheduled').count()

    total_triages = red_count + orange_count + yellow_count + green_count
    if total_triages > 0:
        red_pct = int((red_count / total_triages) * 100)
        orange_pct = int((orange_count / total_triages) * 100)
        yellow_pct = int((yellow_count / total_triages) * 100)
        green_pct = int((green_count / total_triages) * 100)
    else:
        red_pct = orange_pct = yellow_pct = green_pct = 0

    return render(request, 'users/dashboard.html', {
        'today_appointments': today_appointments,
        'emergency_appointments': emergency_appointments,
        'urgent_triages': urgent_triages,
        'completed_appts': completed_appts,
        'canceled_appts': canceled_appts,
        'total_emergencies': total_emergencies,
        'scheduled_appts': scheduled_appts,
        'awaiting_triage': awaiting_triage,
        'red_pct': red_pct,
        'orange_pct': orange_pct,
        'yellow_pct': yellow_pct,
        'green_pct': green_pct,
    })



def logout(request):
    auth_logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('users:login')



@login_required(login_url='users:login')
def register_member(request):
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

    return render(request, 'users/register_member.html')



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



@login_required(login_url='users:login')
def update_member(request, user_id):
    if request.user.role != 'ADM':
        messages.error(request, 'Only Administrators can update team members.')
        return redirect('users:team')

    member = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        member.first_name = request.POST.get('first_name')
        member.last_name = request.POST.get('last_name')
        member.role = request.POST.get('role')
        member.phone = request.POST.get('phone')
        
        email = request.POST.get('email')
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            messages.error(request, 'Email already in use by another user.')
            return redirect('users:update_member', user_id=user_id)
            
        photo = request.FILES.get('photo')
        if photo:
            member.photo = photo

        member.email = email
        member.save()
        
        messages.success(request, 'User updated successfully')
        return redirect('users:team')

    return render(request, 'users/update_member.html', {'member': member})


@login_required(login_url='users:login')
def delete_member(request, user_id):
    if request.user.role != 'ADM':
        messages.error(request, 'Only Administrators can delete team members.')
        return redirect('users:team')

    if request.method == 'POST':
        member = get_object_or_404(User, id=user_id)
        # Prevent admin from deleting themselves
        if member == request.user:
            messages.error(request, 'You cannot delete yourself.')
        else:
            member.delete()
            messages.success(request, 'User deleted successfully')
            
    return redirect('users:team')