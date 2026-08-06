from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
import uuid



class Client(models.Model):
    
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {self.email}'




class Animal(models.Model):

    SPECIE_CHOICES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('reptile', 'Reptile'),
        ('rabbit', 'Rabbit'),
        ('hamsters', 'Hamsters'),
        ('other', 'Other'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Unknown'),
    ]

    owner = models.ForeignKey(Client, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    specie = models.CharField(max_length=100, choices=SPECIE_CHOICES)
    breed = models.CharField(max_length=100)
    gender = models.CharField(max_length=100, choices=GENDER_CHOICES, default='U')
    date_of_birth = models.DateField(null=True, blank=True)
    is_estimated_dob = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='pets/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} - {(self.specie)} | {self.owner}'




class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    REASON_CHOICES = [
        ('routine', 'Routine Check-up'),
        ('vaccine', 'Vaccination'),
        ('illness', 'Illness / Sickness'),
        ('emergency', 'Emergency'),
        ('surgery', 'Surgery'),
        ('followup', 'Follow-up'),
        ('other', 'Other'),
    ]

    DURATION_CHOICES = [
        (30, '30 min'),
        (60, '1 h'),
        (90, '1 h 30 min'),
        (120, '2 h'),
        (150, '2 h 30 min'),
        (180, '3 h'),
        (210, '3 h 30 min'),
        (240, '4 h'),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='appointments')
    veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='appointments',
        limit_choices_to={'role': 'VET'}
    )
    scheduled_at = models.DateTimeField()
    duration = models.IntegerField(choices=DURATION_CHOICES, default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default='routine')
    notes = models.TextField(blank=True, null=True)
    
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.animal} | {self.scheduled_at} | {self.status}'

    def clean(self):
        # Emergency: pre-select current time
        if self.reason == 'emergency':
            self.scheduled_at = timezone.now()

        # Overlapping appointment validation
        if self.scheduled_at and self.veterinarian:
            end_time = self.scheduled_at + timedelta(minutes=self.duration)
            
            start_of_day = self.scheduled_at.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            appointments_that_day = Appointment.objects.filter(
                veterinarian=self.veterinarian,
                scheduled_at__gte=start_of_day,
                scheduled_at__lt=end_of_day
            ).exclude(status='canceled')

            if self.pk:
                appointments_that_day = appointments_that_day.exclude(pk=self.pk)

            for appt in appointments_that_day:
                appt_end_time = appt.scheduled_at + timedelta(minutes=appt.duration)
                
                if self.scheduled_at < appt_end_time and end_time > appt.scheduled_at:
                    raise ValidationError({'scheduled_at': 'The veterinarian already has an appointment scheduled that conflicts with this time.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)




class Triage(models.Model):

    RISK_LEVEL_CHOICES = [
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('orange', 'Orange'),
        ('red', 'Red'),
    ]
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    heart_rate = models.IntegerField()
    respiratory_rate = models.IntegerField()
    temperature = models.FloatField()
    weight = models.FloatField()
    complaint = models.TextField()
    notes = models.TextField()
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.animal} - {self.risk_level}'




class MedicalRecord(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='medical_records')
    
    veterinarian = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='medical_records',
        limit_choices_to={'role': 'VET'}
    )
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_records')

    triage = models.ForeignKey(Triage, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_records')
    
    consultation_media = models.FileField(upload_to='consultations/media/', null=True, blank=True)

    ai_transcription_consultation = models.TextField(blank=True, null=True)

    ai_summary_consultation = models.TextField(blank=True, null=True)
    
    exam_pdf = models.FileField(upload_to='consultations/exams/', null=True, blank=True)

    ai_exam_ocr_text = models.TextField(blank=True, null=True)

    ai_exam_interpretation = models.JSONField(blank=True, null=True)
    
    clinical_note = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Medical Record - {self.animal.name} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant')
    ]
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role} message for {self.animal.name} at {self.created_at.strftime("%Y-%m-%d %H:%M")}'