from django.urls import path
from . import views


app_name = 'clients'

urlpatterns = [
    path('new_client/', views.new_client, name='new_client'),
]