from socialdistribution.models import Author, FollowRequest


def unread_follow_requests_count(request):
    if not request.user.is_authenticated:
        return {"unread_follow_requests_count": 0}

    author, _ = Author.objects.get_or_create(user=request.user)
    count = FollowRequest.objects.filter(
        to_author=author,
        status="PENDING",
        seen_by_target=False,
    ).count()
    return {"unread_follow_requests_count": count}
