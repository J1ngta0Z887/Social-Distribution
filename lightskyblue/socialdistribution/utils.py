from markdown_it import MarkdownIt
from django.utils.html import escape
import requests
from .models import ProcessedEvent, Entry
from django.db import transaction, IntegrityError

def render_content(content, content_type):
    if content_type == "text/markdown":
        # Task 10: Render Markdown
        md = MarkdownIt()
        return md.render(content)
    else:
        # Task 11: Escape Plain Text (Security)
        return f"<p>{escape(content)}</p>"

def fetch_github_events(username):
    url = f"https://api.github.com/users/{username}/events/public"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "lightskyblue-socialdistribution",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data =  response.json() 
        return data if isinstance(data, list) else []
    
    except requests.RequestException as e:
        return []

def human_readable_github_content(event):
    etype = event.get("type", "GitHub Event")
    repo = event.get("repo", {}).get("name", "Unknown Repo")
    actor = event.get("actor", {}).get("login", "Unknown User")
    return f"{actor} performed {etype} on {repo}"

def new_events(author, username):
    events = fetch_github_events(username)
    if not isinstance(events, list):
        return []
    
    processed_ids = set(ProcessedEvent.objects.filter(author=author).values_list("event_id", flat=True))
    for event in events:
        event_id = event.get("id")
        # now we need to check if this event_id has already been processed for this user
        if not event_id or event_id in processed_ids:
            continue
        # create a public entry for this event
        try:
            with transaction.atomic():
                # to make these enteries to be done together
                ProcessedEvent.objects.create(author=author, event_id=event_id)
                Entry.objects.create(
                    author=author,
                    title=f"GitHub Event: {event.get('type')}",
                    content=human_readable_github_content(event),
                    content_type="text/plain",
                    visibility="PUBLIC",
                )
        except IntegrityError:
            # If the entry already exists, skip it
            continue
        # mark this event as processed
        processed_ids.add(event_id)



