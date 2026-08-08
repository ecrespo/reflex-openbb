"""news_feed component (T-305).

REQ: REQ-004

Renders a list of news items as rx.card.
"No recent news" if the list is empty (REQ-004 O-where: the system
shall display a placeholder if no news is available).
"""

from __future__ import annotations

import reflex as rx

__all__ = ["news_feed"]


def _news_card(item) -> rx.Component:
    """A single news card."""
    return rx.card(
        rx.vstack(
            rx.heading(item.title, size="3"),
            rx.text(
                f"{item.source} · {item.published_at.strftime('%Y-%m-%d %H:%M')}",
                color="gray.500",
                size="2",
            ),
            rx.link(
                "Read more",
                href=str(item.url),
                is_external=True,
                color="blue.9",
                size="2",
            ),
            align="start",
            spacing="2",
        ),
        size="2",
        width="100%",
    )


def news_feed(news: list) -> rx.Component:
    """Render a list of news items.

    Args:
        news: list of NewsItem objects. Empty list shows placeholder.
    """
    if not news:
        return rx.center(
            rx.text("No recent news", color="gray.500", size="3"),
            padding="4",
        )
    return rx.vstack(
        *[_news_card(item) for item in news],
        spacing="3",
        width="100%",
    )
