from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "archive_events.py"


class ArchiveEventsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.index = Path(self.tempdir.name) / "index.html"
        self.sitemap = Path(self.tempdir.name) / "sitemap.xml"
        shutil.copy(ROOT / "index.html", self.index)
        shutil.copy(ROOT / "sitemap.xml", self.sitemap)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_archive(self, today: str) -> str:
        result = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--today",
                today,
                "--index",
                str(self.index),
                "--sitemap",
                str(self.sitemap),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def test_event_stays_upcoming_during_its_date(self) -> None:
        output = self.run_archive("2026-11-20")
        html = self.index.read_text(encoding="utf-8")
        self.assertIn("Non hai eventos que arquivar", output)
        self.assertIn('data-event-date="2026-11-20"', html)
        self.assertNotIn('data-archived-date="2026-11-20"', html)

    def test_first_event_moves_to_history_the_next_day(self) -> None:
        self.run_archive("2026-11-21")
        html = self.index.read_text(encoding="utf-8")
        self.assertNotIn('data-event-date="2026-11-20"', html)
        self.assertIn('data-archived-date="2026-11-20"', html)
        self.assertIn('id="comunicacion-2026-11-20"', html)
        self.assertIn('<time datetime="2026">2026</time><span>CIIL 2026</span>', html)
        self.assertNotIn("EDIFICIO REDEIRAS · UNIVERSIDADE DE VIGO", html)
        self.assertIn('data-event-date="2026-11-26"', html)
        self.assertNotIn("data-upcoming-section hidden", html)
        self.assertIn("<lastmod>2026-11-21</lastmod>", self.sitemap.read_text())

    def test_all_events_archive_in_reverse_chronological_order(self) -> None:
        self.run_archive("2026-11-27")
        html = self.index.read_text(encoding="utf-8")
        silg = html.index('data-archived-date="2026-11-26"')
        ciil = html.index('data-archived-date="2026-11-20"')
        self.assertLess(silg, ciil)
        self.assertIn("data-upcoming-section hidden", html)
        self.assertIn("data-upcoming-link hidden", html)

    def test_second_run_is_idempotent(self) -> None:
        self.run_archive("2026-11-27")
        first_html = self.index.read_text(encoding="utf-8")
        output = self.run_archive("2026-11-28")
        self.assertEqual(first_html, self.index.read_text(encoding="utf-8"))
        self.assertIn("Non hai eventos que arquivar", output)


if __name__ == "__main__":
    unittest.main()
