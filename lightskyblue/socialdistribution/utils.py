from markdown_it import MarkdownIt
from django.utils.html import escape


def render_content(content, content_type):
    if content_type == "text/markdown":
        # Task 10: Render Markdown
        md = MarkdownIt()
        return md.render(content)
    else:
        # Task 11: Escape Plain Text (Security)
        return f"<p>{escape(content)}</p>"
