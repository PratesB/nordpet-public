from django.urls import path
from . import views



app_name = 'users'


urlpatterns = [
    path('', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),
    path('team/new/', views.register_team, name='register_team'),
    path('team/', views.team, name='team'),
]