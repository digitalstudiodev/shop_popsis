from django.urls import path, include
from .views import (register, profile, login_view, logout_view)

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('profile/', profile, name='profile'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]