from django.urls import path, include
import os
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'user'
urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='sign-in'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('view/profile/id=<id>/', views.view_profile, name='view_profile'),
    path('add/money/', views.add_money, name='add_money'),
    path('view/transactions/', views.view_transactions, name='transactions'),
    path('view/cart/user_id/', views.cart_info, name='cart_info'),
    path('add/new/account/', views.add_account, name='add_account'),
    path('add/code/', views.PromoCode, name = 'offers'),
    path('cart/checkout/', views.Checkout, name = 'Checkout'),
]
