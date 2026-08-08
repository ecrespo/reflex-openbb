"""news_feed component (T-305).

REQ: REQ-004

Renders a list of news items.

Two calling patterns are supported:
1. **Production**: state pre-renders news as `list[str]` of HTML.
2. **Test**: pass `list[NewsItem]` and we serialize to HTML here.
"""

from __future__ import annotations

from html import escape

import reflex as rx

from reflex_openbb.data.types import NewsItem

__all__ = ["news_feed"]


def _news_to_html(n: NewsItem) -> str:
    """Convert a single NewsItem to an HTML string."""
    title = escape(n.title)
    source = escape(n.source)
    when = escape(n.published_at.strftime("%Y-%m-%d %H:%M"))
    url = escape(str(n.url))
    return (
        f'<div class="news-card">'
        f'<h3>{title}</h3>'
        f'<p class="meta">{source} · {when}</p>'
        f'<a href="{url}" target="_blank" rel="noopener">Read more</a>'
        f'</div>'
    )


def _news_to_html_list(news) -> list[str]:
    """Convert a list[NewsItem] to list[str] of HTML."""
    return [_news_to_html(n) for n in news]


def _is_var(obj) -> bool:
    return hasattr(obj, "_var_type") or hasattr(obj, "length")


def _list(news) -> rx.Component:
    """The list of news items rendered with dangerouslySetInnerHTML."""
    return rx.vstack(
        rx.foreach(
            news,
            lambda html: rx.box(
                dangerously_set_inner_html=html,
                class_name="news-card",
                padding="3",
                border="1px solid var(--gray-a4)",
                border_radius="var(--radius-2)",
            ),
        ),
        spacing="3",
        width="100%",
    )


def _empty_state() -> rx.Component:
    return rx.center(
        rx.text("No recent news", color="gray.500", size="3"),
        padding="4",
    )


def news_feed(news, has_data=None) -> rx.Component:
    """Render a list of news items.

    Args:
        news: list[str] (or Var) of HTML — production path.
              list[NewsItem] — test path, will be serialized.
        has_data: bool (or Var). If None, inferred from len(news).
    """
    if has_data is None:
        # Infer from the data itself
        if _is_var(news):
            has_data = news.length() > 0
        else:
            has_data = len(news) > 0
            if has_data and not isinstance(news[0], str):
                # Convert Pydantic list to HTML strings (test path)
                news = _news_to_html_list(news)
    if _is_var(news):
        return rx.cond(has_data, _list(news), _empty_state())
    if not has_data:
        return _empty_state()
    return _list(news)
