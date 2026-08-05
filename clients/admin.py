from django.contrib import admin
from .models import Client, Animal, Appointment, Triage, MedicalRecord, ChatMessage


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone')
    ordering = ('-created_at',)
    

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'specie', 'breed', 'gender', 'owner', 'date_of_birth', 'is_estimated_dob')
    list_filter = ('specie', 'gender', 'owner', 'is_estimated_dob')
    search_fields = ('name', 'specie', 'breed', 'gender', 'owner__name', 'is_estimated_dob')
    ordering = ('-created_at',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'animal', 'veterinarian', 'scheduled_at', 'status', 'reason')
    list_filter = ('status', 'reason', 'scheduled_at')
    search_fields = ('animal__name', 'veterinarian__first_name', 'veterinarian__email', 'status', 'reason')
    ordering = ('-scheduled_at',)


@admin.register(Triage)
class TriageAdmin(admin.ModelAdmin):
    list_display = ('id', 'animal', 'risk_level', 'heart_rate', 'respiratory_rate', 'temperature', 'weight', 'created_at')
    list_filter = ('risk_level', 'created_at')
    search_fields = ('animal__name', 'complaint')
    ordering = ('-created_at',)


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'animal', 'veterinarian', 'appointment', 'created_at')
    list_filter = ('created_at', 'veterinarian')
    search_fields = ('animal__name', 'veterinarian__first_name', 'veterinarian__email', 'clinical_note')
    ordering = ('-created_at',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'animal', 'role', 'sender', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('animal__name', 'content')
    ordering = ('-created_at',)