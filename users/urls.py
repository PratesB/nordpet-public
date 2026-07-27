from django.urls import path
from . import views



app_name = 'users'


urlpatterns = [
    path('', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),
    path('team/new/', views.register_member, name='register_member'),
    path('team/', views.team, name='team'),
    path('team/<uuid:user_id>/update/', views.update_member, name='update_member'),
    path('team/<uuid:user_id>/delete/', views.delete_member, name='delete_member'),
]