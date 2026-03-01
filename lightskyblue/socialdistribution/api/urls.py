# ref: https://docs.djangoproject.com/en/6.0/topics/http/urls/

from django.urls import path
from . import views
from .views import AuthorsAPI, AuthorAPI, AuthorFollowingsAPI

urlpatterns = [
    #
    path("authors", AuthorsAPI.as_view()),
    path("authors/<int:author_id>", AuthorAPI.as_view()),
    path("authors/<int:author_id>/following", AuthorFollowingsAPI.as_view())
]