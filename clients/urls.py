from django.urls import path
from . import views


app_name = 'clients'

urlpatterns = [
    path('new_client/', views.new_client, name='new_client'),
    path('appointment/new/', views.new_appointment, name='new_appointment'),
    path('appointment/<uuid:pk>/edit/', views.update_appointment, name='update_appointment'),
    path('appointment/<uuid:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('api/available-times/', views.get_available_times, name='api_available_times'),
    path('appointments/', views.appointments_dashboard, name='appointments'),
    path('patients/', views.patients, name='patients'),
    path('update-patient/<int:pk>/', views.update_patient, name='update_patient'),
    path('delete-patient/<int:pk>/', views.delete_patient, name='delete_patient'),
]