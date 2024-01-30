from django.urls import path
from . import views

app_name = 'calc'
urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('main/', views.main, name='main'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),

    path('common/', views.common, name='common'),
    path('common/career', views.common_career, name="cc"),
    path('common/wp', views.common_workperformance, name="cw"),
    path('common/training', views.common_training, name="ct"),
]
