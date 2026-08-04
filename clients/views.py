from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Client, Animal, Appointment, Triage, MedicalRecord
from datetime import datetime, timedelta
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
import os


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
            return redirect('clients:appointments')

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
        'veterinarians': User.objects.filter(role='VET', is_active=True),
        'durations': Appointment.DURATION_CHOICES,
        'reasons': Appointment.REASON_CHOICES,
        'time_slots': time_slots,
        'preselected_animal_id': request.GET.get('animal_id'),
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
            return redirect('clients:appointments')
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
        try:
            appointment = Appointment.objects.filter(pk=pk).first()
            if appointment:
                appointment.status = 'canceled'
                appointment.save()
                messages.success(request, 'Appointment canceled successfully!')
            else:
                messages.error(request, 'Appointment not found.')
        except Exception as e:
            messages.error(request, f'An error occurred while canceling: {str(e)}')
    else:
        messages.error(request, 'Invalid request method.')
        
    return redirect('clients:appointments')


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

    now = timezone.now()
    available_slots = []
    for slot in time_slots:
        slot_dt = timezone.make_aware(datetime.combine(query_date, slot))
        
        # Do not allow past times
        if slot_dt < now:
            continue
            
        is_busy = False
        for appt in appointments:
            appt_end = appt.scheduled_at + timedelta(minutes=appt.duration)
            if appt.scheduled_at <= slot_dt < appt_end:
                is_busy = True
                break
        if not is_busy:
            available_slots.append(slot.strftime("%H:%M"))

    return JsonResponse({'available_times': available_slots})

@login_required(login_url='users:login')
def appointments_dashboard(request):
    date_str = request.GET.get('date')
    today = timezone.localdate()
    
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = today
    else:
        target_date = today

    selected_vet_id = request.GET.get('vet_id', '')
    vets = User.objects.filter(role='VET', is_active=True)

    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=7)

    day_appointments = Appointment.objects.filter(
        scheduled_at__date=target_date,
        status__in=['scheduled', 'completed']
    )
    week_appointments = Appointment.objects.filter(
        scheduled_at__date__gte=start_of_week,
        scheduled_at__date__lt=end_of_week,
        status__in=['scheduled', 'completed']
    )

    if selected_vet_id:
        day_appointments = day_appointments.filter(veterinarian_id=selected_vet_id)
        week_appointments = week_appointments.filter(veterinarian_id=selected_vet_id)

    columns_data = []
    if selected_vet_id:
        columns_data.append({
            'is_today': target_date == today,
            'label_name': target_date.strftime('%b %d'),
            'vet_id': selected_vet_id
        })
    else:
        for vet in vets:
            columns_data.append({
                'is_today': target_date == today,
                'label_name': f"Dr. {vet.first_name or vet.email.split('@')[0]}",
                'vet_id': vet.id
            })

    grid_rows = []
    for hour in range(7, 21):
        cols = []
        for col_def in columns_data:
            vet_id = col_def['vet_id']
            
            # Use make_aware with the min time
            hour_start = timezone.make_aware(datetime.combine(target_date, datetime.min.time().replace(hour=hour)))
            hour_end = hour_start + timedelta(hours=1)

            col_appts_objs = day_appointments.filter(
                veterinarian_id=vet_id,
                scheduled_at__gte=hour_start,
                scheduled_at__lt=hour_end
            )

            col_appts = []
            for appt in col_appts_objs:
                local_dt = timezone.localtime(appt.scheduled_at)
                minute = local_dt.minute
                top = minute
                height = appt.duration
                
                col_appts.append({
                    'obj': appt,
                    'top': top,
                    'height': height,
                    'left_pct': 0,
                    'width_pct': 100,
                    'time_str': f"{local_dt.strftime('%H:%M')} - {(local_dt + timedelta(minutes=appt.duration)).strftime('%H:%M')}"
                })
            
            if len(col_appts) > 1:
                width = 100 / len(col_appts)
                for i, c_appt in enumerate(col_appts):
                    c_appt['left_pct'] = i * width
                    c_appt['width_pct'] = width

            cols.append(col_appts)
            
        grid_rows.append({
            'hour_label': f"{hour:02d}:00",
            'cols': cols
        })

    context = {
        'current_month_year': target_date.strftime('%B %Y'),
        'prev_date': (target_date - timedelta(days=1)).strftime('%Y-%m-%d'),
        'today_date': today.strftime('%Y-%m-%d'),
        'next_date': (target_date + timedelta(days=1)).strftime('%Y-%m-%d'),
        'relative_label': 'Today' if target_date == today else target_date.strftime('%b %d'),
        'day_stat_label': 'Today' if target_date == today else 'Selected Day',
        'day_appointments_count': day_appointments.count(),
        'week_stat_label': 'This Week',
        'week_appointments_count': week_appointments.count(),
        'vet_query': f"&vet_id={selected_vet_id}" if selected_vet_id else "",
        'vets': vets,
        'selected_vet_id': selected_vet_id,
        'view_mode': 'day',
        'columns_data': columns_data,
        'grid_rows': grid_rows
    }

    return render(request, 'clients/appointments.html', context)


@login_required(login_url='users:login')
def patients(request):
    name = request.GET.get('name', '')
    owner = request.GET.get('owner', '')
    specie = request.GET.get('specie', '')

    patients = Animal.objects.select_related('owner').all().order_by('-created_at')

    if name:
        patients = patients.filter(name__icontains=name)
    if owner:
        patients = patients.filter(owner__name__icontains=owner)
    if specie:
        patients = patients.filter(specie=specie)

    patients_with_visits = []

    for animal in patients:
        last_visit = animal.appointments.filter(status='completed').order_by('-scheduled_at').first()
        patients_with_visits.append({
            'animal': animal,
            'last_visit': last_visit
        })
    
    context = {
        'patients_with_visits': patients_with_visits,
        'name': name,
        'owner': owner,
        'specie': specie,
    }
    return render(request, 'clients/patients.html', context)


@login_required(login_url='users:login')
def update_patient(request, pk):
    animal = get_object_or_404(Animal, pk=pk)
    client = animal.owner
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                client.name = request.POST.get('name', client.name)
                client.email = request.POST.get('email', client.email)
                client.phone = request.POST.get('phone', client.phone)
                client.save()

                animal.name = request.POST.get('animal_name', animal.name)
                animal.specie = request.POST.get('specie', animal.specie)
                animal.breed = request.POST.get('breed', animal.breed)
                animal.gender = request.POST.get('gender', animal.gender)
                
                dob_str = request.POST.get('date_of_birth')
                is_estimated = request.POST.get('estimate_date') == 'on'
                photo = request.FILES.get('petPhoto')
                
                if dob_str:
                    animal.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                animal.is_estimated_dob = is_estimated
                if photo:
                    animal.photo = photo
                animal.save()
            
            messages.success(request, 'Patient updated successfully!')
            return redirect('clients:patients')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('clients:update_patient', pk=pk)

    context = {
        'animal': animal,
        'client': client,
    }
    return render(request, 'clients/update_patient.html', context)


@login_required(login_url='users:login')
def delete_patient(request, pk):
    if request.method == 'POST':
        animal = get_object_or_404(Animal, pk=pk)
        animal.delete()
        messages.success(request, 'Patient deleted successfully!')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('clients:patients')


@login_required(login_url='users:login')
def add_pet(request, client_id):
    client = get_object_or_404(Client, pk=client_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                new_pet = Animal.objects.create(
                    owner=client,
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
            
            messages.success(request, f'Pet added successfully to {client.name}!')
            return redirect('clients:patients')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('clients:add_pet', client_id=client.id)

    return render(request, 'clients/add_pet.html', {'client': client})


@login_required(login_url='users:login')
def client_list(request):
    clients = Client.objects.prefetch_related('animal_set').all().order_by('-created_at')
    
    name = request.GET.get('name', '')
    since_date = request.GET.get('since_date', '')
    
    if name:
        clients = clients.filter(name__icontains=name)
        
    if since_date:
        try:
            target_date = datetime.strptime(since_date, '%Y-%m-%d').date()
            clients = clients.filter(created_at__date=target_date)
        except ValueError:
            pass
        
    context = {
        'clients': clients,
        'name': name,
        'since_date': since_date
    }
    return render(request, 'clients/client_list.html', context)


@login_required(login_url='users:login')
def update_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        try:
            client.name = request.POST.get('name', client.name)
            client.email = request.POST.get('email', client.email)
            client.phone = request.POST.get('phone', client.phone)
            client.save()
            messages.success(request, f'Client {client.name} updated successfully!')
            return redirect('clients:client_list')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('clients:update_client', pk=pk)

    return render(request, 'clients/update_client.html', {'client': client})


@login_required(login_url='users:login')
def delete_client(request, pk):
    if request.method == 'POST':
        client = get_object_or_404(Client, pk=pk)
        client.delete()
        messages.success(request, 'Client and their pets were deleted successfully!')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('clients:client_list')



@login_required(login_url='users:login')
def upload_medical_record(request, pet_id):
    if request.user.role not in ['ADM', 'VET']:
        messages.error(request, 'You do not have permission to attach exams or notes.')
        return redirect('clients:patients')

    if request.method == 'POST':
        pet = get_object_or_404(Animal, id=pet_id)
        consultation_media = request.FILES.get('consultation_media')
        exam_pdf = request.FILES.get('exam_pdf')
        clinical_note = request.POST.get('clinical_note')
        appointment_id = request.POST.get('appointment_id')
        
        if consultation_media or exam_pdf or clinical_note:
            try:
                target_appointment = None
                if appointment_id == 'standalone':
                    target_appointment = None
                elif appointment_id:
                    target_appointment = Appointment.objects.filter(id=appointment_id, animal=pet).first()
                else:
                    today = timezone.now().date()
                    target_appointment = Appointment.objects.filter(
                        animal=pet,
                        scheduled_at__date=today,
                        status__in=['scheduled', 'in_progress']
                    ).first()
                
                triage = Triage.objects.filter(animal=pet).order_by('-created_at').first()
                
                record = MedicalRecord(
                    animal=pet,
                    veterinarian=request.user if request.user.role == 'VET' else None,
                    appointment=target_appointment,
                    triage=triage,
                )
                
                if consultation_media:
                    record.consultation_media = consultation_media
                if exam_pdf:
                    record.exam_pdf = exam_pdf
                if clinical_note:
                    record.clinical_note = clinical_note
                    
                record.save()
                    
                messages.success(request, 'Record updated successfully.')
            except Exception as e:
                messages.error(request, f'An error occurred while saving the record: {str(e)}')
        else:
            messages.error(request, 'No file or text was provided.')
            
    return redirect('clients:medical_record', pet_id=pet_id)



@login_required(login_url='users:login')
def medical_record(request, pet_id):
    if request.user.role not in ['ADM', 'VET']:
        messages.error(request, 'You do not have permission to view medical records.')
        return redirect('clients:patients')

    pet = get_object_or_404(Animal, id=pet_id)
    triage = Triage.objects.filter(animal=pet).order_by('-created_at').first()
    medical_records = pet.medical_records.all().order_by('-created_at')
    
    # Find any active appointment for today
    today = timezone.now().date()   
    active_appointment = Appointment.objects.filter(
        animal=pet,
        scheduled_at__date=today,
        status__in=['scheduled', 'in_progress']
    ).first()
    
    triage_today = Triage.objects.filter(animal=pet, created_at__date=today).exists()
    
    appointments = list(pet.appointments.all().order_by('-scheduled_at'))
    completed_appointments = []
    
    
    for appt in appointments:
        # Find triage done on the same day as the appointment
        triage_obj = Triage.objects.filter(
            animal=pet,
            created_at__date=appt.scheduled_at.date()
        ).first()
        
        appt_records = list(appt.medical_records.all())
        
        if appt.status == 'completed' or appt_records or triage_obj:
            appt.type = 'appointment'
            appt.triage_obj = triage_obj
            for rec in appt_records:
                rec.exam_pdf_filename = os.path.basename(rec.exam_pdf.name) if rec.exam_pdf else ''
                rec.consultation_media_filename = os.path.basename(rec.consultation_media.name) if rec.consultation_media else ''
            appt.records_list = appt_records
            completed_appointments.append(appt)

    standalone_records = pet.medical_records.filter(appointment__isnull=True).order_by('-created_at')
    standalone_events = list(standalone_records)
    for rec in standalone_events:
        rec.type = 'standalone_record'
        rec.exam_pdf_filename = os.path.basename(rec.exam_pdf.name) if rec.exam_pdf else ''
        rec.consultation_media_filename = os.path.basename(rec.consultation_media.name) if rec.consultation_media else ''
        rec.scheduled_at = rec.created_at 

    timeline = completed_appointments + standalone_events
    timeline.sort(key=lambda x: x.scheduled_at, reverse=True)

    context = {
        'pet': pet,
        'triage': triage,
        'triage_today': triage_today,
        'medical_records': medical_records,
        'latest_record': medical_records.first(),
        'active_appointment': active_appointment,
        'appointments': appointments,
        'timeline': timeline,
    }
    return render(request, 'clients/medical_record.html', context)



@login_required(login_url='users:login')
def start_consultation(request, pet_id):
    if request.user.role != 'VET':
        messages.error(request, 'Only veterinarians can start consultations.')
        return redirect('clients:medical_record', pet_id=pet_id)

    today = timezone.now().date()
    appointment = Appointment.objects.filter(
        animal_id=pet_id,
        scheduled_at__date=today,
        status='scheduled',
        veterinarian=request.user
    ).first()
    
    if appointment:
        appointment.status = 'in_progress'
        if not appointment.started_at:
            appointment.started_at = timezone.now()
        appointment.save()
        messages.success(request, 'Consultation started successfully.')
    else:
        messages.error(request, 'No scheduled consultation found for you today for this pet.')
        
    return redirect('clients:medical_record', pet_id=pet_id)


@login_required(login_url='users:login')
def end_consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.user.role != 'VET':
        messages.error(request, 'Only veterinarians can end consultations.')
        return redirect('clients:medical_record', pet_id=appointment.animal.id)

    if appointment.veterinarian != request.user:
        messages.error(request, 'You can only end your own consultations.')
        return redirect('clients:medical_record', pet_id=appointment.animal.id)

    if appointment.status == 'in_progress':
        appointment.status = 'completed'
        appointment.ended_at = timezone.now()
        appointment.save()
        messages.success(request, 'Consultation completed successfully.')
        
    return redirect('clients:medical_record', pet_id=appointment.animal.id)



@login_required(login_url='users:login')
def triage(request, pet_id):
    pet = get_object_or_404(Animal, id=pet_id)

    today = timezone.now().date()
    
    appointment_today = pet.appointments.filter(scheduled_at__date=today).exists()
    
    if not appointment_today:
        messages.warning(request, 'This patient does not have an appointment today.')
        return redirect('clients:patients')

    triage = Triage.objects.filter(animal=pet, created_at__date=today).first()

    if request.method == 'POST':
        if triage:
            messages.error(request, 'A triage has already been completed for this patient today.')
            return redirect('clients:triage', pet_id=pet.id)
        try:
            heart_rate = int(request.POST.get('heart_rate'))
            respiratory_rate = int(request.POST.get('respiratory_rate'))
            temperature = float(request.POST.get('temperature'))
            weight = float(request.POST.get('weight'))
            complaint = request.POST.get('complaint', '').strip()
            notes = request.POST.get('notes', '').strip()

            if not complaint:
                raise ValueError("Complaint cannot be empty")
                
        except (ValueError, TypeError):
            messages.error(request, 'Please ensure all vital signs are valid numbers and the tutor complaint is filled out.')
            return redirect('clients:triage', pet_id=pet.id)

        # Triage Logic (simplified for now)
        risk_level = 'green'
        
        complaint_lower = complaint.lower()
        red_keywords = ['seizure', 'unconscious', 'bleeding', 'choking', 'poison', 'hit by car', 'fainting']
        orange_keywords = ['vomit', 'diarrhea', 'pain', 'fracture']
        yellow_keywords = ['lethargic', 'fever', 'itching', 'scratching']
        
        if any(word in complaint_lower for word in red_keywords):
            risk_level = 'red'
        elif any(word in complaint_lower for word in orange_keywords):
            risk_level = 'orange'
        elif any(word in complaint_lower for word in yellow_keywords):
            risk_level = 'yellow'
            
        # Check vital signs extremes
        if temperature > 40.0 or temperature < 36.0:
            risk_level = 'red'
        elif temperature > 39.5 or temperature < 37.0:
            if risk_level in ['green', 'yellow']:
                risk_level = 'orange'
                
        if heart_rate > 180 or heart_rate < 50:
            if risk_level in ['green', 'yellow']:
                risk_level = 'orange'
        if heart_rate > 220 or heart_rate < 40:
            risk_level = 'red'
            
        if respiratory_rate > 60 or respiratory_rate < 15:
            if risk_level == 'green':
                risk_level = 'yellow'
        if respiratory_rate > 80 or respiratory_rate < 10:
            risk_level = 'red'
            
        triage = Triage.objects.create(
            animal=pet,
            heart_rate=heart_rate,
            respiratory_rate=respiratory_rate,
            temperature=temperature,
            weight=weight,
            complaint=complaint,
            notes=notes,
            risk_level=risk_level
        )
        

        return redirect('clients:triage', pet_id=pet.id)

    return render(request, 'clients/triage.html', {'pet': pet, 'triage': triage})