from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Client, Animal
from datetime import datetime
from django.db import transaction
from django.contrib import messages



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
            return HttpResponse("create new appointment page")
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('clients:new_client')

    return render(request, 'clients/new_client.html')