from django.contrib import admin
from django.urls import path, include
from . import views

app_name = 'home'
urlpatterns = [
    path('', views.home, name='EMS-home'),
    path('search/', views.search_results, name = 'search')
]
