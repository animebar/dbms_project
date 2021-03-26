from django.urls import path

from . import views
app_name = 'events'
urlpatterns = [
    path('view/event_id=<id>', views.view_event, name='view_event'),
    path('book/event_id=<id>', views.book_event, name='book_event')
]
