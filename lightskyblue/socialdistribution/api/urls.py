# ref: https://docs.djangoproject.com/en/6.0/topics/http/urls/

from django.urls import path
from . import views
from .views import AuthorsView

urlpatterns = [
    #
    path("authors", AuthorsView.as_view())
]