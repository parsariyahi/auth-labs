from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('oauth2/callback/', views.oauth_callback, name='oauth_callback'),
    path('profile/', views.profile, name='profile'),
] 