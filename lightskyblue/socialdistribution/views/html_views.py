from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.db.models import Q
from ..utils import new_events
from ..models import Author, Entry, Comment, FollowRequest
from ..forms import AuthorForm, EntryForm, CommentForm
from django.views.decorators.http import require_POST, require_GET




@login_required
def home(request):
    # update the announcement to show the latest github events for the user
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    if me.github_url:
        # extract the username from the github url
        username = me.github_url.rstrip("/").split("/")[-1]
        new_events(me, username)
    return render(request, "socialdistribution/home.html")


@login_required
def authors_list(request):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    authors = Author.objects.filter(host=me.host)

    q = request.GET.get("q")  # ← added
    if q:                     # ← added
        authors = authors.filter(user__username__icontains=q)

    return render(request, "socialdistribution/authors.html", {
        "authors": authors,
        "my_author": me
    })


@login_required
def follow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    target = get_object_or_404(Author, id=author_id)

    if me.host != target.host:
        return HttpResponseForbidden("Can only follow local authors")

    if me.id == target.id:
        return HttpResponseBadRequest("Cannot follow yourself")

    fr, _ = FollowRequest.objects.get_or_create(from_author=me, to_author=target)
    # If previously rejected, allow re-request and mark it unread again.
    if fr.status == "REJECTED":
        fr.status = "PENDING"
        fr.seen = False
        fr.save(update_fields=["status", "seen"])
    return redirect(request.META.get('HTTP_REFERER', 'authors_list'))

@login_required
def follow_requests(request):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    pending = FollowRequest.objects.filter(to_author=me, status="PENDING").select_related("from_author__user")
    pending.filter(seen=False).update(seen=True)
    return render(request, "socialdistribution/follow_requests.html", {
        "follow_requests": pending,
        "my_author": me,
    })

@require_POST
@login_required
def handle_follow_request(request, request_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    fr = get_object_or_404(FollowRequest, id=request_id, to_author=me)

    action = request.POST.get("action")
    if action == "accept":
        fr.status = "ACCEPTED"
        fr.save(update_fields=["status"])
        fr.from_author.following.add(fr.to_author)
    elif action == "reject":
        fr.status = "REJECTED"
        fr.save(update_fields=["status"])
    else:
        return HttpResponseBadRequest("Invalid action")

    return redirect("follow_requests")

@login_required
def unfollow_local_author(request, author_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    target = get_object_or_404(Author, id=author_id)

    me.following.remove(target)
    return redirect(request.META.get('HTTP_REFERER', 'authors_list'))


@login_required
def my_entries(request):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    entries = Entry.objects.filter(author=me).order_by("-created_at")
    return render(request, "socialdistribution/my_entries.html", {
        "my_author": me,
        "entries": entries,
    })


@login_required
def create_entry(request):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})

    if request.method == "POST":
        form = EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.author = me
            entry.save()
            return redirect("home")
    else:
        form = EntryForm()

    return render(request, "socialdistribution/create_entry.html", {
        "my_author": me,
        "form": form,
    })


@login_required
def author_entries(request, author_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    author = get_object_or_404(Author, id=author_id)

    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors' entries")

    all_entries = Entry.objects.filter(author=author).order_by("-created_at")
    entries = [e for e in all_entries if can_access_entry(me, e)]

    return render(request, "socialdistribution/author_entries.html", {
        "my_author": me,
        "author": author,
        "entries": entries,
    })

def can_access_entry(me: Author, entry: Entry) -> bool:
    if entry.visibility == "PUBLIC":
        return True
    if entry.author == me:
        return True
    if entry.author.host != me.host:
        return False

    following_ids = set(me.following.values_list("id", flat=True))
    friend_ids = set(me.following.filter(following=me).values_list("id", flat=True))

    if entry.visibility == "UNLISTED":
        return entry.author_id in following_ids  
    elif entry.visibility == "FRIENDS":
        return entry.author_id in friend_ids
    return False


@login_required
def feed(request):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})

    following_ids = set(me.following.values_list("id", flat=True))
    following_ids.add(me.id)
    friend_ids = set(me.following.filter(following=me).values_list("id", flat=True))

    #allows viewing of all public entries and unlisted/friends-only entries of authors you are following
    entries = Entry.objects.filter(author__host=me.host).filter(
        Q(visibility="PUBLIC") |
        Q(visibility="UNLISTED", author__id__in=following_ids) |
        Q(visibility="FRIENDS", author__id__in=friend_ids)
    ).order_by("-created_at")
    
    return render(request, "socialdistribution/feed.html", {
        "my_author": me,
        "entries": entries,
    })


@login_required
def public_author_profile(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    author, _ = Author.objects.get_or_create(user=user, defaults={"display_name": user.username})

    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})

    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors")

    # If it's your own profile, show all your entries (optional)
    if request.user == user:
        entries = Entry.objects.filter(author=author).order_by("-created_at")
    else:
        # Non-followers (and everyone else) only see PUBLIC posts
        all_entries = Entry.objects.filter(author=author).order_by("-created_at")
        entries = [e for e in all_entries if can_access_entry(me, e)]
    followers_count = author.followers.count()
    following_count = author.following.count()
    friends_count = author.following.filter(following=author).count()

    return render(request, "socialdistribution/profile.html", {
        "profile_user": user,
        "author": author,
        "entries": entries,
        "my_author": me,
        "followers_count": followers_count,
        "following_count": following_count,
        "friends_count": friends_count,
    })

@login_required
def author_followers(request, author_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    author = get_object_or_404(Author, id=author_id)

    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors")

    followers = author.followers.select_related("user").order_by("user__username")
    return render(request, "socialdistribution/author_connections.html", {
        "connection_type": "Followers",
        "author": author,
        "connections": followers,
        "my_author": me,
    })

@login_required
def author_following(request, author_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    author = get_object_or_404(Author, id=author_id)

    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors")

    following = author.following.select_related("user").order_by("user__username")
    return render(request, "socialdistribution/author_connections.html", {
        "connection_type": "Following",
        "author": author,
        "connections": following,
        "my_author": me,
    })

@login_required
def author_friends(request, author_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    author = get_object_or_404(Author, id=author_id)

    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors")

    friends = author.following.filter(followers=author).select_related("user").order_by("user__username")
    return render(request, "socialdistribution/author_connections.html", {
        "connection_type": "Friends",
        "author": author,
        "connections": friends,
        "my_author": me,
    })

@login_required
def edit_profile(request):
    author, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})

    if request.method == "POST":
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            form.save()
            return redirect("public_author_profile", username=request.user.username)
    else:
        form = AuthorForm(instance=author)

    return render(request, "socialdistribution/edit_profile.html", {
        "form": form,
        "author": author,
    })

@login_required
def edit_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)

    # Task 13: Security Check - Other authors cannot modify my entries
    # We compare the Entry's author's user to the Request's user
    if entry.author.user != request.user:
        return HttpResponseForbidden("You are not the author of this entry.")

    if request.method == "POST":
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect("my_entries") # Redirects to the list of user's entries
    else:
        form = EntryForm(instance=entry)

    # Reusing the create_entry template, or you can make a specific edit_entry.html
    return render(request, "socialdistribution/create_entry.html", {
        "form": form,
        "title": "Edit Entry"
    })

@login_required
def delete_entry(request, entry_id):
    entry = get_object_or_404(Entry, id=entry_id)

    # Task 13: Security Check
    if entry.author.user != request.user:
        return HttpResponseForbidden("You are not the author of this entry.")

    if request.method == "POST":
        entry.delete()
        return redirect(request.POST.get("next") or "home")

    # Task 23: Author can see entry before deletion (It's passed in context)
    return render(request, "socialdistribution/confirm_delete.html", {"entry": entry})

@require_POST
@login_required
def add_comment(request, entry_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    entry = get_object_or_404(Entry, id=entry_id)

    if not can_access_entry(me, entry):
        return HttpResponseForbidden("You cannot comment on this entry.")

    form = CommentForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid comment.")

    comment = form.save(commit=False)
    comment.entry = entry
    comment.author = me
    comment.save()

    return redirect(request.POST.get("next") or "feed")


@require_POST
@login_required
def toggle_entry_like(request, entry_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    entry = get_object_or_404(Entry, id=entry_id)

    if not can_access_entry(me, entry):
        return HttpResponseForbidden("You cannot like this entry.")

    if entry.likes.filter(id=me.id).exists():
        entry.likes.remove(me)
    else:
        entry.likes.add(me)

    return redirect(request.POST.get("next") or "feed")


@require_POST
@login_required
def toggle_comment_like(request, comment_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    comment = get_object_or_404(Comment, id=comment_id)
    entry = comment.entry

    # same access rule as the entry
    if not can_access_entry(me, entry):
        return HttpResponseForbidden("You cannot like this comment.")

    if comment.likes.filter(id=me.id).exists():
        comment.likes.remove(me)
    else:
        comment.likes.add(me)

    return redirect(request.POST.get("next") or "feed")

@require_GET
@login_required
def view_entry(request, entry_id):
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    entry = get_object_or_404(Entry, id=entry_id)
    
    # Check if user can access this entry
    if not can_access_entry(me, entry):
        return HttpResponseForbidden("You cannot view this entry.")
    
    return render(request, "socialdistribution/view_entry.html", {
        "entry": entry,
        "my_author": me,
    })
