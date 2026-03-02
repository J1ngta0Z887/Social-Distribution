"""HTML views 

Format:
- Request fields are path/query/form values (type, example, purpose).
- Response fields are template context values or redirect targets.
- All endpoints require login and are not paginated.

Visibility:
- PUBLIC: visible to local users.
- UNLISTED: visible to followers.
- FRIENDS: visible to mutual followers.

Endpoints:
-------------------------------------------------
- `GET /` (`feed`): main timeline; use for browsing posts.
  Request: none. Response: `my_author: Author`, `entries: QuerySet[Entry]`.
  Examples: `GET /`, refresh `GET /` after posting.

- `GET /authors/` (`authors_list`): browse local authors.
  Query: `q: str` (ex `"har"`) for username filtering.
  Response: `authors: QuerySet[Author]`, `my_author: Author`.
  Examples: `GET /authors/`, `GET /authors/?q=chris`.

- `POST /authors/<author_id>/follow/` and `/unfollow/`:
  follow/unfollow local authors; do not use for self or remote authors.
  Path: `author_id: int` (ex `12`). Response: `302` redirect.
  Examples: `POST /authors/12/follow/`, `POST /authors/12/unfollow/`.

- `GET /follow-requests/`, `POST /follow-requests/<request_id>/handle/`:
  review and handle follow requests.
  Path: `request_id: int` (ex `7`), Form: `action: str` (`accept|reject`).
  Response: list template or `302` redirect.
  Examples: `GET /follow-requests/`, `POST ... action=accept`.

- `GET /author/<username>/`, `/authors/<author_id>/(followers|following|friends)/`:
  view profile and social graph.
  Path: `username: str` or `author_id: int`.
  Response includes author objects and count/list context fields.
  Examples: `GET /author/harneetk/`, `GET /authors/12/friends/`.

- `GET|POST /profile/edit/`:
  edit current user profile only.
  Form: `display_name: str`, `bio: str`, `picture_url: url`, `github_url: url`.
  Response: form template or `302` redirect to own profile.
  Examples: `GET /profile/edit/`, `POST /profile/edit/`.

- `GET /entries/`, `GET|POST /entries/new/`,
  `GET /authors/<author_id>/entries/`, `GET /entries/<entry_id>/`:
  list own entries, create entries, view author entries, view one entry.
  Paths: `author_id: int`, `entry_id: int`.
  Create form: `title: str`, `content: str`, `image_url: url`,
  `visibility: str`, `content_type: str`.
  Examples: `GET /entries/`, `POST /entries/new/`, `GET /entries/33/`.

- `GET|POST /entries/<entry_id>/edit/` and `/delete/`:
  owner-only edit/delete operations.
  Path: `entry_id: int`; delete form optional `next: str`.
  Response: form/confirm template or `302` redirect.
  Examples: `GET /entries/33/edit/`, `POST /entries/33/delete/`.

- `POST /entries/<entry_id>/comment/`, `/entries/<entry_id>/like/`,
  `/comments/<comment_id>/like/`:
  comment/like toggles on accessible content.
  Paths: `entry_id: int`, `comment_id: int`.
  Form: `content: str` (comment), optional `next: str` (redirect target).
  Response: `302` redirect.
  Examples: `POST /entries/33/comment/`, `POST /entries/33/like/`.

Note:
- `home(request)` exists but root URL is currently wired to `feed`.
"""

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
    """Render home and refresh GitHub activity for the current author."""
    # Refresh GitHub activity shown on the home page.
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    if me.github_url:
        # Extract username from the profile URL.
        username = me.github_url.rstrip("/").split("/")[-1]
        new_events(me, username)
    return render(request, "socialdistribution/home.html")


@login_required
def authors_list(request):
    """Render local authors with optional username filtering."""
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    authors = Author.objects.filter(host=me.host)

    q = request.GET.get("q")
    if q:
        authors = authors.filter(user__username__icontains=q)

    return render(request, "socialdistribution/authors.html", {
        "authors": authors,
        "my_author": me
    })


@login_required
def follow_local_author(request, author_id):
    """Create or reopen a follow request to another local author."""
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
    """Show pending follow requests and mark unseen requests as seen."""
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
    """Accept or reject an incoming follow request."""
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
    """Remove a local author from the current author's following list."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    target = get_object_or_404(Author, id=author_id)

    me.following.remove(target)
    return redirect(request.META.get('HTTP_REFERER', 'authors_list'))


@login_required
def my_entries(request):
    """List entries authored by the current user."""
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    entries = Entry.objects.filter(author=me).order_by("-created_at")
    return render(request, "socialdistribution/my_entries.html", {
        "my_author": me,
        "entries": entries,
    })


@login_required
def create_entry(request):
    """Create a new entry for the current author."""
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
    """List entries from a local author that the requester can access."""
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
    """Return whether `me` can access `entry` under visibility rules."""
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
    """Render the feed with relationship-aware visibility filters."""
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})

    following_ids = set(me.following.values_list("id", flat=True))
    following_ids.add(me.id)
    friend_ids = set(me.following.filter(following=me).values_list("id", flat=True))

    # Include local public entries and relationship-limited entries.
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
    """Render a local author profile with entries visible to the requester."""
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    author, _ = Author.objects.get_or_create(user=user, defaults={"display_name": user.username})

    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})

    if me.host != author.host:
        return HttpResponseForbidden("Can only view local authors")

    # Owners can always see all of their own entries.
    if request.user == user:
        entries = Entry.objects.filter(author=author).order_by("-created_at")
    else:
        # Non-owners are filtered by visibility rules.
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
    """Render the followers list for a local author."""
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
    """Render the following list for a local author."""
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
    """Render the mutual-follow (friends) list for a local author."""
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
    """Edit profile fields for the current author."""
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
    """Edit an entry if and only if the requester is its author."""
    entry = get_object_or_404(Entry, id=entry_id)

    # Only the entry owner can edit.
    if entry.author.user != request.user:
        return HttpResponseForbidden("You are not the author of this entry.")

    if request.method == "POST":
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect("my_entries")
    else:
        form = EntryForm(instance=entry)

    # Reuse the create-entry template in edit mode.
    return render(request, "socialdistribution/create_entry.html", {
        "form": form,
        "title": "Edit Entry"
    })

@login_required
def delete_entry(request, entry_id):
    """Delete an entry if and only if the requester is its author."""
    entry = get_object_or_404(Entry, id=entry_id)

    # Only the entry owner can delete.
    if entry.author.user != request.user:
        return HttpResponseForbidden("You are not the author of this entry.")

    if request.method == "POST":
        entry.delete()
        return redirect(request.POST.get("next") or "home")

    return render(request, "socialdistribution/confirm_delete.html", {"entry": entry})

@require_POST
@login_required
def add_comment(request, entry_id):
    """Create a comment on an entry the requester can access."""
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
    """Toggle the requester's like on an entry they can access."""
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
    """Toggle the requester's like on a comment in an accessible entry."""
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    comment = get_object_or_404(Comment, id=comment_id)
    entry = comment.entry

    # Apply the same access gate used for entries.
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
    """Render a single entry if the requester has access."""
    me, _ = Author.objects.get_or_create(user=request.user, defaults={"display_name": request.user.username})
    entry = get_object_or_404(Entry, id=entry_id)
    
    if not can_access_entry(me, entry):
        return HttpResponseForbidden("You cannot view this entry.")
    
    return render(request, "socialdistribution/view_entry.html", {
        "entry": entry,
        "my_author": me,
    })
