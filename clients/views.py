from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Client, Animal, Appointment
from datetime import datetime, timedelta
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()



@login_required(login_url='users:login')
def new_client(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                new_client = Client.objects.create(
                    name=request.POST.get('name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                )

                new_pet = Animal.objects.create(
                    owner=new_client,
                    name=request.POST.get('animal_name'),
                    specie=request.POST.get('specie'),
                    breed=request.POST.get('breed'),
                    gender=request.POST.get('gender'),
                )
                
                dob_str = request.POST.get('date_of_birth')
                is_estimated = request.POST.get('estimate_date') == 'on'
                photo = request.FILES.get('petPhoto')
                
                if dob_str:
                    new_pet.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                new_pet.is_estimated_dob = is_estimated
                if photo:
                    new_pet.photo = photo
                new_pet.save()
            
            messages.success(request, 'Client and pet registered successfully!')
            return redirect('clients:new_appointment')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('clients:new_client')

    return render(request, 'clients/new_client.html')

@login_required(login_url='users:login')
def new_appointment(request):
    if request.method == 'POST':
        try:
            date_str = request.POST.get('appointment_date')
            time_str = request.POST.get('appointment_time')
            scheduled_at_str = f"{date_str}T{time_str}" if date_str and time_str else None
            
            if scheduled_at_str:
                naive_dt = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
                scheduled_at = timezone.make_aware(naive_dt)
            else:
                scheduled_at = None
            
            appointment = Appointment(
                animal_id=request.POST.get('animal'),
                veterinarian_id=request.POST.get('veterinarian') or None,
                scheduled_at=scheduled_at,
                duration=int(request.POST.get('duration', 30)),
                reason=request.POST.get('reason'),
                notes=request.POST.get('notes', '')
            )
            # The full_clean() inside save() will trigger all validations
            appointment.save()
            messages.success(request, 'Appointment scheduled successfully!')
            return HttpResponse("Appointment Dashboard") #TODO: add redirect

        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            
    # Generate time slots from 07:00 to 20:00
    time_slots = []
    for h in range(7, 21):
        time_slots.append(f"{h:02d}:00")
        if h != 20:
            time_slots.append(f"{h:02d}:30")

    context = {
        'animals': Animal.objects.all(),
        'veterinarians': User.objects.filter(role='VET'),
        'durations': Appointment.DURATION_CHOICES,
        'reasons': Appointment.REASON_CHOICES,
        'time_slots': time_slots,
    }
    return render(request, 'clients/new_appointment.html', context)

@login_required(login_url='users:login')
def update_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        try:
            date_str = request.POST.get('appointment_date')
            time_str = request.POST.get('appointment_time')
            if date_str and time_str:
                scheduled_at_str = f"{date_str}T{time_str}"
                naive_dt = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
                appointment.scheduled_at = timezone.make_aware(naive_dt)
            
            appointment.animal_id = request.POST.get('animal')
            appointment.veterinarian_id = request.POST.get('veterinarian') or None
            appointment.duration = int(request.POST.get('duration', appointment.duration))
            appointment.reason = request.POST.get('reason')
            appointment.notes = request.POST.get('notes', '')
            
            appointment.save()
            messages.success(request, 'Appointment updated successfully!')
            return HttpResponse("Appointment Dashboard") #TODO: add redirect
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            
    # Generate time slots from 07:00 to 20:00
    time_slots = []
    for h in range(7, 21):
        time_slots.append(f"{h:02d}:00")
        if h != 20:
            time_slots.append(f"{h:02d}:30")
            
    context = {
        'appointment': appointment,
        'animals': Animal.objects.all(),
        'veterinarians': User.objects.filter(role='VET'),
        'durations': Appointment.DURATION_CHOICES,
        'reasons': Appointment.REASON_CHOICES,
        'time_slots': time_slots,
    }
    return render(request, 'clients/new_appointment.html', context)

@login_required(login_url='users:login')
def cancel_appointment(request, pk):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, pk=pk)
        appointment.status = 'canceled'
        appointment.save()
        messages.success(request, 'Appointment canceled successfully!')
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return HttpResponse("Appointment Dashboard")
    return HttpResponse(status=405)


@login_required(login_url='users:login')
def get_available_times(request):
    date_str = request.GET.get('date')
    vet_id = request.GET.get('vet_id')
    appointment_id = request.GET.get('appointment_id')

    if not date_str or not vet_id:
        return JsonResponse({'error': 'Missing date or vet_id'}, status=400)

    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Generate all slots
    time_slots = []
    for h in range(7, 21):
        time_slots.append(datetime.strptime(f"{h:02d}:00", "%H:%M").time())
        if h != 20:
            time_slots.append(datetime.strptime(f"{h:02d}:30", "%H:%M").time())

    # Get appointments for this vet on this day
    start_of_day = timezone.make_aware(datetime.combine(query_date, datetime.min.time()))
    end_of_day = start_of_day + timedelta(days=1)
    
    appointments = Appointment.objects.filter(
        veterinarian_id=vet_id,
        scheduled_at__gte=start_of_day,
        scheduled_at__lt=end_of_day
    ).exclude(status='canceled')

    if appointment_id:
        appointments = appointments.exclude(id=appointment_id)

    available_slots = []
    for slot in time_slots:
        slot_dt = timezone.make_aware(datetime.combine(query_date, slot))
        is_busy = False
        for appt in appointments:
            appt_end = appt.scheduled_at + timedelta(minutes=appt.duration)
            if appt.scheduled_at <= slot_dt < appt_end:
                is_busy = True
                break
        if not is_busy:
            available_slots.append(slot.strftime("%H:%M"))

    return JsonResponse({'available_times': available_slots})