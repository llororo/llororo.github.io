#!/usr/bin/env python3
"""Envía un informe diario de Cloudflare Web Analytics cando hai visitas."""

from __future__ import annotations

import html
import json
import os
import smtplib
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


GRAPHQL_ENDPOINT = "https://api.cloudflare.com/client/v4/graphql"
SITE_HOST = "llororo.github.io"
SITE_TAG = "53008120a2c441dcbde2a0dc40a70abf"
LOCAL_TIMEZONE = ZoneInfo("Europe/Berlin")

QUERY = r"""
query DailyWebAnalytics(
  $accountTag: string!
  $siteTag: string!
  $start: Time!
  $end: Time!
) {
  viewer {
    accounts(filter: { accountTag: $accountTag }) {
      total: rumPageloadEventsAdaptiveGroups(
        limit: 1
        filter: {
          siteTag: $siteTag
          datetime_geq: $start
          datetime_lt: $end
        }
      ) {
        count
        sum { visits }
      }
      countries: rumPageloadEventsAdaptiveGroups(
        limit: 100
        orderBy: [count_DESC]
        filter: {
          siteTag: $siteTag
          datetime_geq: $start
          datetime_lt: $end
        }
      ) {
        count
        dimensions { countryName }
      }
      referrers: rumPageloadEventsAdaptiveGroups(
        limit: 100
        orderBy: [count_DESC]
        filter: {
          siteTag: $siteTag
          datetime_geq: $start
          datetime_lt: $end
        }
      ) {
        count
        dimensions { refererHost }
      }
      paths: rumPageloadEventsAdaptiveGroups(
        limit: 100
        orderBy: [count_DESC]
        filter: {
          siteTag: $siteTag
          datetime_geq: $start
          datetime_lt: $end
        }
      ) {
        count
        dimensions { requestPath }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class ReportWindow:
    day: date
    start_utc: datetime
    end_utc: datetime


@dataclass(frozen=True)
class AnalyticsReport:
    day: date
    pageviews: int
    visits: int
    countries: list[tuple[str, int]]
    referrers: list[tuple[str, int]]
    paths: list[tuple[str, int]]


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta a variable obrigatoria {name}")
    return value


def report_window(day_text: str | None = None, now: datetime | None = None) -> ReportWindow:
    if day_text:
        report_day = date.fromisoformat(day_text)
    else:
        current = now or datetime.now(timezone.utc)
        report_day = current.astimezone(LOCAL_TIMEZONE).date() - timedelta(days=1)

    start_local = datetime.combine(report_day, time.min, tzinfo=LOCAL_TIMEZONE)
    end_local = datetime.combine(report_day + timedelta(days=1), time.min, tzinfo=LOCAL_TIMEZONE)
    return ReportWindow(
        day=report_day,
        start_utc=start_local.astimezone(timezone.utc),
        end_utc=end_local.astimezone(timezone.utc),
    )


def iso_utc(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def query_cloudflare(account_id: str, api_token: str, window: ReportWindow) -> dict[str, Any]:
    payload = {
        "query": " ".join(QUERY.split()),
        "variables": {
            "accountTag": account_id,
            "siteTag": SITE_TAG,
            "start": iso_utc(window.start_utc),
            "end": iso_utc(window.end_utc),
        },
    }
    request = Request(
        GRAPHQL_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "User-Agent": "llororo-daily-analytics/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare respondeu con HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Non se puido conectar con Cloudflare: {error.reason}") from error

    if result.get("errors"):
        messages = "; ".join(str(item.get("message", item)) for item in result["errors"])
        raise RuntimeError(f"A consulta de Cloudflare devolveu erros: {messages}")

    accounts = result.get("data", {}).get("viewer", {}).get("accounts", [])
    if not accounts:
        raise RuntimeError("Cloudflare non devolveu datos para a conta indicada")
    return accounts[0]


def safe_count(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def grouped(rows: Iterable[dict[str, Any]], dimension: str, empty_label: str) -> list[tuple[str, int]]:
    values: Counter[str] = Counter()
    for row in rows:
        raw_label = row.get("dimensions", {}).get(dimension)
        label = str(raw_label).strip() if raw_label else empty_label
        values[label] += safe_count(row.get("count"))
    return values.most_common()


def referrer_label(host: str) -> str:
    normalized = host.strip().lower().removeprefix("www.")
    if not normalized or normalized == "acceso directo ou procedencia non dispoñible":
        return "Acceso directo ou procedencia non dispoñible"
    if normalized == SITE_HOST or normalized.endswith(f".{SITE_HOST}"):
        return "Navegación interna"
    if normalized.startswith("google.") or ".google." in normalized:
        return "Google"
    if normalized == "bing.com" or normalized.endswith(".bing.com"):
        return "Bing"
    if normalized == "duckduckgo.com" or normalized.endswith(".duckduckgo.com"):
        return "DuckDuckGo"
    if normalized == "search.brave.com" or normalized.endswith(".search.brave.com"):
        return "Brave Search"
    if normalized == "chatgpt.com" or normalized.endswith(".chatgpt.com"):
        return "ChatGPT"
    return host


def build_report(day: date, data: dict[str, Any]) -> AnalyticsReport:
    total_rows = data.get("total") or []
    total = total_rows[0] if total_rows else {}
    pageviews = safe_count(total.get("count"))
    visits = safe_count(total.get("sum", {}).get("visits"))

    countries = grouped(data.get("countries") or [], "countryName", "País non dispoñible")
    raw_referrers = grouped(
        data.get("referrers") or [],
        "refererHost",
        "Acceso directo ou procedencia non dispoñible",
    )
    referrer_counts: Counter[str] = Counter()
    for host, count in raw_referrers:
        referrer_counts[referrer_label(host)] += count

    paths = grouped(data.get("paths") or [], "requestPath", "/")
    return AnalyticsReport(
        day=day,
        pageviews=pageviews,
        visits=visits,
        countries=countries,
        referrers=referrer_counts.most_common(),
        paths=paths,
    )


def plain_rows(rows: list[tuple[str, int]], limit: int = 10) -> str:
    if not rows:
        return "  Sen datos"
    return "\n".join(f"  {label}: {count}" for label, count in rows[:limit])


def html_rows(rows: list[tuple[str, int]], limit: int = 10) -> str:
    if not rows:
        return "<p>Sen datos</p>"
    items = "".join(
        f"<li><strong>{html.escape(label)}</strong>: {count}</li>"
        for label, count in rows[:limit]
    )
    return f"<ul>{items}</ul>"


def make_message(report: AnalyticsReport, sender: str, recipient: str) -> EmailMessage:
    formatted_day = report.day.strftime("%d.%m.%Y")
    message = EmailMessage()
    message["Subject"] = f"Visitas a llororo.github.io · {formatted_day}"
    message["From"] = sender
    message["To"] = recipient

    message.set_content(
        f"""Informe de visitas de llororo.github.io
Data: {formatted_day}

Visitas: {report.visits}
Páxinas vistas: {report.pageviews}

Países
{plain_rows(report.countries)}

Procedencias
{plain_rows(report.referrers)}

Páxinas consultadas
{plain_rows(report.paths)}

Cloudflare Web Analytics conta accesos nos que se executa o seu código. Os bloqueadores e algúns navegadores poden facer que o total sexa inferior ó tráfico real.
"""
    )
    message.add_alternative(
        f"""<!doctype html>
<html lang="gl"><body style="font-family:Arial,sans-serif;line-height:1.5;color:#111">
<h1 style="font-size:22px">Visitas a llororo.github.io</h1>
<p><strong>Data:</strong> {formatted_day}</p>
<p style="font-size:18px"><strong>Visitas:</strong> {report.visits}<br><strong>Páxinas vistas:</strong> {report.pageviews}</p>
<h2 style="font-size:17px">Países</h2>{html_rows(report.countries)}
<h2 style="font-size:17px">Procedencias</h2>{html_rows(report.referrers)}
<h2 style="font-size:17px">Páxinas consultadas</h2>{html_rows(report.paths)}
<p style="font-size:12px;color:#555">Cloudflare Web Analytics conta accesos nos que se executa o seu código. Os bloqueadores e algúns navegadores poden facer que o total sexa inferior ó tráfico real.</p>
</body></html>""",
        subtype="html",
    )
    return message


def send_message(message: EmailMessage, username: str, password: str) -> None:
    host = os.environ.get("SMTP_HOST", "mail.gmx.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


def main() -> int:
    window = report_window(os.environ.get("REPORT_DATE") or None)
    data = query_cloudflare(
        required_env("CLOUDFLARE_ACCOUNT_ID"),
        required_env("CLOUDFLARE_API_TOKEN"),
        window,
    )
    report = build_report(window.day, data)

    force = os.environ.get("REPORT_FORCE", "").lower() in {"1", "true", "yes"}
    if report.pageviews == 0 and not force:
        print(f"Sen visitas o {window.day.isoformat()}; non se envía correo.")
        return 0

    username = required_env("SMTP_USERNAME")
    recipient = required_env("REPORT_EMAIL")
    message = make_message(report, username, recipient)
    send_message(message, username, required_env("SMTP_PASSWORD"))
    print(f"Informe do {window.day.isoformat()} enviado a {recipient}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1)
