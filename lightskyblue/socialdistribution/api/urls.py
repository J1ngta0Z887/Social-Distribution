# ref: https://docs.djangoproject.com/en/6.0/topics/http/urls/

from django.urls import re_path, path, include
from . import views
from .views import AuthorsAPI, AuthorAPI, AuthorFollowingsAPI, AuthorFollowersAPI, AuthorFollowingPerUserAPI, \
    AuthorFollowRequestAPI

# https://regex101.com/r/1tqPOL/1 (matches either author id or name)
author_id_regex = r"(?P<author_id>[\w\s]+)"
target_author_id_regex = r"(?P<target_author_id>[\w\s]+)"

urlpatterns = [
    # very rough fix for supporting both regular and
    # directory-based paths
    path("authors", include(
        [
            path("", AuthorsAPI.as_view()),
            re_path(author_id_regex, include(
                [
                    path("", AuthorAPI.as_view()),
                    path("/", include([
                        path("following/", include(
                            [
                                path("", AuthorFollowingsAPI.as_view()),
                                re_path(target_author_id_regex, AuthorFollowingPerUserAPI.as_view()),
                        ])),
                        path("following", AuthorFollowingsAPI.as_view()),
                        path("followers", AuthorFollowersAPI.as_view()),
                        path("follow_requests", AuthorFollowRequestAPI.as_view()),
                    ]))
                ]
            )),

        ]
    )),
]
