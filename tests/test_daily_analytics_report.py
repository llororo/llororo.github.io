import importlib.util
from datetime import date, datetime, timezone
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "daily_analytics_report.py"
SPEC = importlib.util.spec_from_file_location("daily_analytics_report", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DailyAnalyticsReportTests(unittest.TestCase):
    def test_previous_berlin_day_is_used(self):
        now = datetime(2026, 10, 23, 5, 30, tzinfo=timezone.utc)
        window = MODULE.report_window(now=now)

        self.assertEqual(window.day, date(2026, 10, 22))
        self.assertEqual(MODULE.iso_utc(window.start_utc), "2026-10-21T22:00:00Z")
        self.assertEqual(MODULE.iso_utc(window.end_utc), "2026-10-22T22:00:00Z")

    def test_report_groups_search_engines_and_empty_referrers(self):
        data = {
            "total": [{"count": 9, "sum": {"visits": 7}}],
            "countries": [
                {"count": 6, "dimensions": {"countryName": "ES"}},
                {"count": 3, "dimensions": {"countryName": "DE"}},
            ],
            "referrers": [
                {"count": 3, "dimensions": {"refererHost": "www.google.es"}},
                {"count": 2, "dimensions": {"refererHost": "google.com"}},
                {"count": 2, "dimensions": {"refererHost": ""}},
                {"count": 1, "dimensions": {"refererHost": "www.bing.com"}},
                {"count": 1, "dimensions": {"refererHost": MODULE.SITE_HOST}},
            ],
            "paths": [{"count": 9, "dimensions": {"requestPath": "/"}}],
        }

        report = MODULE.build_report(date(2026, 10, 22), data)

        self.assertEqual(report.pageviews, 9)
        self.assertEqual(report.visits, 7)
        self.assertEqual(report.referrers[0], ("Google", 5))
        self.assertIn(("Bing", 1), report.referrers)
        self.assertIn(("Navegación interna", 1), report.referrers)
        self.assertIn(("Acceso directo ou procedencia non dispoñible", 2), report.referrers)

    def test_email_contains_requested_sections(self):
        report = MODULE.AnalyticsReport(
            day=date(2026, 10, 22),
            pageviews=4,
            visits=3,
            countries=[("ES", 4)],
            referrers=[("DuckDuckGo", 3)],
            paths=[("/", 4)],
        )

        message = MODULE.make_message(report, "sender@example.com", "recipient@example.com")
        plain = message.get_body(preferencelist=("plain",)).get_content()

        self.assertEqual(message["Subject"], "Visitas a llororo.github.io · 22.10.2026")
        self.assertIn("Visitas: 3", plain)
        self.assertIn("DuckDuckGo: 3", plain)
        self.assertIn("ES: 4", plain)


if __name__ == "__main__":
    unittest.main()
