from django.contrib import admin
from .models import Client, Animal


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