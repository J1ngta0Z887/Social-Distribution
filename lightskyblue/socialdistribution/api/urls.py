# ref: https://docs.djangoproject.com/en/6.0/topics/http/urls/

from django.urls import path

from .views import api_authors
from .views_old import (
    AuthorAPI,
    AuthorFollowersAPI,
    AuthorFollowingPerUserAPI,
    AuthorFollowingsAPI,
    AuthorFollowRequestAPI,
    AuthorsAPI,
)

# https://regex101.com/r/1tqPOL/1 (matches either author id or name)
author_id_regex = r"(?P<author_id>[\w\s]+)"
target_author_id_regex = r"(?P<target_author_id>[\w\s]+)"

urlpatterns = [
    # very rough fix for supporting both regular and
    # directory-based paths
    path("authors/", api_authors.as_view())
]
