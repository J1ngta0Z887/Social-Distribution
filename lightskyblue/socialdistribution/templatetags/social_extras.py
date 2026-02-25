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