from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", LoginView.as_view(template_name="socialdistribution/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("author/<str:username>/", views.public_author_profile, name="public_author_profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("authors/", views.authors_list, name="authors_list"),
    path("authors/<int:author_id>/follow/", views.follow_local_author, name="follow_local_author"),
    path("authors/<int:author_id>/unfollow/", views.unfollow_local_author, name="unfollow_local_author"),
    path("feed/", views.feed, name="feed"),
    path("entries/", views.my_entries, name="my_entries"),
    path("entries/new/", views.create_entry, name="create_entry"),
    path("authors/<int:author_id>/entries/", views.author_entries, name="author_entries"),
    path('entries/<int:entry_id>/edit/', views.edit_entry, name='edit_entry'),
    path('entries/<int:entry_id>/delete/', views.delete_entry, name='delete_entry'),
]