from django.db import models
from django.conf import settings



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