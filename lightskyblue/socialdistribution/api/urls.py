# ref: https://docs.djangoproject.com/en/6.0/topics/http/urls/

from django.urls import include, path, re_path

from .views import (
    api_authors,
    api_authors_の,
    api_authors_の_entries,
    api_authors_の_entries_よ,
    api_authors_の_followers_よ,
    api_authors_の_following,
    api_authors_の_following_よ,
    api_authors_の_followくrequests,
    api_entries_よ,
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
    path(
        "authors/<str:author_id>/followers/<path:other_author_id>/",
        api_authors_の_followers_よ.as_view(),
    ),
    path(
        "authors/<str:author_id>/follow_requests/",
        api_authors_の_followくrequests.as_view(),
    ),
    path(
        "authors/<str:author_id>/entries/<str:entry_id>",
        api_authors_の_entries_よ.as_view(),
    ),
    path("entries/<path:entry_id>", api_entries_よ.as_view()),
    path(
        "authors/<str:target_author_id>/entries",
        api_authors_の_entries.as_view(),
    ),
    path(
        "authors/<str:target_author_id>/entries/",
        api_authors_の_entries.as_view(),
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
