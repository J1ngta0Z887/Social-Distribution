from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", LoginView.as_view(template_name="socialdistribution/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),  
    path("author/<str:username>/", views.public_author_profile, name="public_author_profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("authors/<uuid:author_id>/follow/", views.follow_local_author, name="follow_local_author"),
    path("authors/<uuid:author_id>/unfollow/", views.unfollow_local_author, name="unfollow_local_author"),
    path("authors/", views.authors_list, name="authors_list"),
    path("feed/following/", views.following_feed, name="following_feed"),
]