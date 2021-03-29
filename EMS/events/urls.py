from django.urls import path
import os
from . import views


app_name = 'events'
urlpatterns = [
    path('view/event_id=<id>', views.view_event, name='view_event'),
    path('book/event_id=<id>', views.book_event, name='book_event'),
    path('host', views.host_event, name='host_event'),
    path('add/venue/', views.add_venue, name='add_venue'),
    path('add/offers/event_id=<id>', views.add_discount, name = 'offers'),
    path('add/review/event_id=<id>/', views.add_review, name='add_review'),
    path('add/cart/event_id=<id>/', views.insert_cart, name='insert_cart'),
    path('remove/cart/event_id=<id>/', views.remove_cart, name='remove_cart'),
    path('del/cart/event_id=<id>', views.del_cart, name='del_cart'),
    path('increase/cart/event_id=<id>', views.increase_cart, name='increase_cart'),
    path('decrease/cart/event_id=<id>', views.decrease_cart, name='decrease_cart')

]

