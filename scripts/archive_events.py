#!/usr/bin/env python3
"""Move past communications from the upcoming block to the archive."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "index.html"
DEFAULT_SITEMAP = ROOT / "sitemap.xml"
SITE_TIMEZONE = ZoneInfo("Europe/Berlin")

ARTICLE_RE = re.compile(
    r'(?P<indent>^[ \t]*)<article class="upcoming-item" '
    r'id="(?P<id>[^"]+)" data-cv-item '
    r'data-event-date="(?P<date>\d{4}-\d{2}-\d{2})" '
    r'data-event-code="(?P<code>[^"]+)">\n'
    r'(?P<body>.*?)'
    r'^(?P=indent)</article>[ \t]*\n?',
    re.MULTILINE | re.DOTALL,
)

BODY_RE = re.compile(
    r'<p class="upcoming-event">(?P<event>.*?)</p>\s*'
    r'<h4><cite>(?P<title>.*?)</cite>\s*'
    r'<a class="item-anchor" href="#[^"]+"[^>]*>#</a></h4>\s*'
    r'<p>(?P<authors>.*?)</p>',
    re.DOTALL,
)


@dataclass(frozen=True)
class Event:
    item_id: str
    event_date: date
    code: str
    title: str
    authors: str

    @property
    def displayed_date(self) -> str:
        return self.event_date.strftime("%d.%m.%Y")

def parse_today(value: str | None) -> date:
    if value:
        return date.fromisoformat(value)
    return datetime.now(SITE_TIMEZONE).date()


def render_history_entry(event: Event) -> str:
    return (
        '          <li class="entry reveal" '
        f'id="{event.item_id}" data-cv-item '
        f'data-archived-date="{event.event_date.isoformat()}">\n'
        '            <div class="entry-meta">'
        f'<time datetime="{event.event_date.year}">{event.event_date.year}</time>'
        f'<span>{event.code}</span></div>\n'
        '            <div class="entry-body">\n'
        f'              <h3><cite>{event.title}</cite> <a class="item-anchor" href="#{event.item_id}" aria-label="Ligazón directa a esta comunicación">#</a></h3>\n'
        f'              <p>{event.authors}</p>\n'
        '            </div>\n'
        '          </li>\n'
    )


def set_hidden(html: str, marker: str, hidden: bool) -> str:
    pattern = re.compile(rf'(<[^>]+\s{re.escape(marker)})(?:\shidden)?(>)')

    def replace(match: re.Match[str]) -> str:
        hidden_attribute = " hidden" if hidden else ""
        return f"{match.group(1)}{hidden_attribute}{match.group(2)}"

    updated, count = pattern.subn(replace, html, count=1)
    if count != 1:
        raise ValueError(f"Non se atopou o marcador {marker}")
    return updated


def archive_events(html: str, today: date) -> tuple[str, list[Event]]:
    archived: list[Event] = []

    def replace_article(match: re.Match[str]) -> str:
        event_date = date.fromisoformat(match.group("date"))
        if event_date >= today:
            return match.group(0)

        details = BODY_RE.search(match.group("body"))
        if not details:
            raise ValueError(f"Non se puido interpretar o evento do {event_date}")

        archived.append(
            Event(
                item_id=match.group("id"),
                event_date=event_date,
                code=match.group("code"),
                title=details.group("title").strip(),
                authors=details.group("authors").strip(),
            )
        )
        return ""

    updated = ARTICLE_RE.sub(replace_article, html)
    if not archived:
        return html, []

    archive_marker = '        <ol class="entry-list compact" data-archive-target>\n'
    if archive_marker not in updated:
        raise ValueError("Non se atopou a lista histórica de comunicacións")

    entries = "\n".join(
        render_history_entry(event)
        for event in sorted(archived, key=lambda item: item.event_date, reverse=True)
    )
    updated = updated.replace(archive_marker, archive_marker + entries + "\n", 1)

    has_upcoming = ARTICLE_RE.search(updated) is not None
    updated = set_hidden(updated, "data-upcoming-section", not has_upcoming)
    updated = set_hidden(updated, "data-upcoming-link", not has_upcoming)
    return updated, archived


def update_sitemap(sitemap: str, today: date) -> str:
    updated, count = re.subn(
        r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
        f"<lastmod>{today.isoformat()}</lastmod>",
        sitemap,
        count=1,
    )
    if count != 1:
        raise ValueError("Non se atopou lastmod no sitemap")
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--today", help="Data de proba en formato AAAA-MM-DD")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--sitemap", type=Path, default=DEFAULT_SITEMAP)
    args = parser.parse_args()

    today = parse_today(args.today)
    html = args.index.read_text(encoding="utf-8")
    updated_html, archived = archive_events(html, today)
    if not archived:
        print(f"Non hai eventos que arquivar o {today.isoformat()}.")
        return 0

    sitemap = args.sitemap.read_text(encoding="utf-8")
    args.index.write_text(updated_html, encoding="utf-8")
    args.sitemap.write_text(update_sitemap(sitemap, today), encoding="utf-8")
    print(f"Arquiváronse {len(archived)} evento(s):")
    for event in archived:
        print(f"- {event.displayed_date}: {event.code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
