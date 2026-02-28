# ref: https://docs.djangoproject.com/en/6.0/topics/http/urls/

from django.urls import path
from . import views
from .views import AuthorsAPI, AuthorAPI

urlpatterns = [
    #
    path("authors", AuthorsAPI.as_view()),
    path("author/<int:author_id>", AuthorAPI.as_view())
]