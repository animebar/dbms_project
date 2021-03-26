from django.urls import path,include

from . import views
app_name = 'user'
urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='sign-in'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('view/profile/id=<id>',views.view_profile, name='view_profile')
]
