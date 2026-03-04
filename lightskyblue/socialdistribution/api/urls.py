# ref: https://docs.djangoproject.com/en/6.0/topics/http/urls/

from django.urls import include, path, re_path

from .views import (
    api_authors,
    api_authors_の,
    api_authors_の_following,
    api_authors_の_following_よ,
)

# https://regex101.com/r/1tqPOL/1 (matches either author id or name)


def make_id_regex(name):
    return rf"(?P<{name}>[\w\s%:.\/]+)"


urlpatterns = [
    # very rough fix for supporting both regular and
    # directory-based paths
    path("authors", api_authors.as_view()),
    path("authors/", api_authors.as_view()),
    path("authors/<str:author_id>/", api_authors_の.as_view()),
    path("authors/<str:author_id>/following/", api_authors_の_following.as_view()),
    path(
        "authors/<str:author_id>/following/<path:other_author_id>/",
        api_authors_の_following_よ.as_view(),
    ),
    # path(
    #     "authors/",
    #     include(
    #         [
    #             path("", api_authors.as_view()),
    #             re_path(
    #                 make_id_regex("author_id") + "/",
    #                 include(
    #                     [
    #                         path("", api_authors_の.as_view()),
    #                         path(
    #                             "following",
    #                             include(
    #                                 [
    #                                     path("", api_authors_の_following.as_view()),
    #                                     path(
    #                                         "<str:other_author_id>",
    #                                         api_authors_の_following_よ.as_view(),
    #                                     ),
    #                                     # re_path(
    #                                     #     make_id_regex("other_author_id"),
    #                                     #     api_authors_の_following_よ.as_view(),
    #                                     # ),
    #                                 ]
    #                             ),
    #                         ),
    #                     ]
    #                 ),
    #             ),
    #         ]
    #     ),
    # ),
]
