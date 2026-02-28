from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import html_views, api_views

urlpatterns = [
    #HTML pages
    path("", html_views.home, name="home"),
    path("login/", LoginView.as_view(template_name="socialdistribution/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("author/<str:username>/", html_views.public_author_profile, name="public_author_profile"),
    path("profile/edit/", html_views.edit_profile, name="edit_profile"),
    path("authors/", html_views.authors_list, name="authors_list"),
    path("authors/<int:author_id>/follow/", html_views.follow_local_author, name="follow_local_author"),
    path("authors/<int:author_id>/unfollow/", html_views.unfollow_local_author, name="unfollow_local_author"),
    path("feed/", html_views.feed, name="feed"),
    path("entries/", html_views.my_entries, name="my_entries"),
    path("entries/new/", html_views.create_entry, name="create_entry"),
    path("authors/<int:author_id>/entries/", html_views.author_entries, name="author_entries"),
    path("entries/<int:entry_id>/", html_views.view_entry, name="view_entry"),
    path('entries/<int:entry_id>/edit/', html_views.edit_entry, name='edit_entry'),
    path('entries/<int:entry_id>/delete/', html_views.delete_entry, name='delete_entry'),
    path("entries/<int:entry_id>/comment/", html_views.add_comment, name="add_comment"),
    path("entries/<int:entry_id>/like/", html_views.toggle_entry_like, name="toggle_entry_like"),
    path("comments/<int:comment_id>/like/", html_views.toggle_comment_like, name="toggle_comment_like"),
    path("entries/<int:entry_id>/comment/", html_views.add_comment, name="add_comment"),

    #API endpoints
    #path("api/authors/<int:author_id>/entries/<int:entry_id>/", api_views.get_entry, name="api_get_entry"),
    path("follow-requests/", html_views.follow_requests, name="follow_requests"),
    path("follow-requests/<int:request_id>/handle/", html_views.handle_follow_request, name="handle_follow_request"),

]