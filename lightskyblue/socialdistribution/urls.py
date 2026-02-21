from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", LoginView.as_view(template_name="socialdistribution/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),  
    path("author/<str:username>/", views.public_author_profile, name="public_author_profile"),
]