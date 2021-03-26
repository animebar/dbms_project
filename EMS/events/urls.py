from django.urls import path

from . import views
app_name = 'events'
urlpatterns = [
    path('view/event_id=<id>', views.view_event, name='view_event'),
    path('host', views.host_event, name='host_event'),
    path('add/venue/', views.add_venue, name='add_venue'),
]
