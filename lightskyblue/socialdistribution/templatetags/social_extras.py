from django import template
from django.utils.safestring import mark_safe
from ..utils import render_content

register = template.Library()

@register.filter
def render_entry(entry):
    """
    Usage in HTML: {{ entry|render_entry }}
    """
    rendered_html = render_content(entry.content, entry.content_type)
    return mark_safe(rendered_html)

@register.filter
def is_following(user_author, other_author):
    """
    Check if user_author is following other_author.
    Usage in HTML: {% if my_author|is_following:entry.author %}...{% endif %}
    """
    if not user_author or not other_author:
        return False
    return other_author in user_author.following.all()