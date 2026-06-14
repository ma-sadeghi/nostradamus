"""Template context processors shared across all pages."""

from . import quotes


def quote(request):
    """A random quote for the prophecy line, refreshed on every page load."""
    return {"quote": quotes.random()}
