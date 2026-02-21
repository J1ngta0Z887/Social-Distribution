from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Author

@login_required
def follow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me = get_object_or_404(Author, user=request.user)

    target = get_object_or_404(Author, id=author_id)

    if me.host != target.host:
        return HttpResponseForbidden("Can only follow local authors")

    if me.id == target.id:
        return HttpResponseBadRequest("Cannot follow yourself")

    me.following.add(target)
    return JsonResponse({"ok": True, "following": True, "target": str(target.id)})

@login_required
def unfollow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me = get_object_or_404(Author, user=request.user)
    target = get_object_or_404(Author, id=author_id)

    me.following.remove(target)
    return JsonResponse({"ok": True, "following": False, "target": str(target.id)})