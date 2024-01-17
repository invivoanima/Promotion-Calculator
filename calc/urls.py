from django.urls import path
from . import views

app_name = 'calc'
urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('main/', views.main, name='main'),
    path('login/', views.login, name='login'),
]
