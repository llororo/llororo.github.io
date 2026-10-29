import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_page_date.py"
SPEC = importlib.util.spec_from_file_location("update_page_date", MODULE_PATH)
page_date = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = page_date
SPEC.loader.exec_module(page_date)


DOCUMENT = """<!doctype html><html><head>
<script type="application/ld+json">{"dateModified":"2026-01-10T12:00:00+01:00"}</script>
</head><body><main><h1>Web</h1></main><footer>
<!-- page-updated:start -->
<p class="page-updated">ÚLTIMA ACTUALIZACIÓN: <time datetime="2026-01-10">10.01.2026</time></p>
<!-- page-updated:end -->
</footer></body></html>
"""


class PageDateTests(unittest.TestCase):
    def git(self, repo, *args, env=None):
        subprocess.run(("git", *args), cwd=repo, check=True, env=env, stdout=subprocess.PIPE)

    def commit(self, repo, message, date):
        env = {
            "PATH": os.environ["PATH"],
            "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_DATE": date,
        }
        self.git(repo, "add", ".", env=env)
        self.git(repo, "commit", "-m", message, env=env)

    def make_repo(self):
        temporary = tempfile.TemporaryDirectory()
        repo = Path(temporary.name)
        self.git(repo, "init", "-b", "master")
        self.git(repo, "config", "user.name", "Test")
        self.git(repo, "config", "user.email", "test@example.com")
        (repo / "index.html").write_text(DOCUMENT, encoding="utf-8")
        (repo / "styles.css").write_text("body { color: black; }\n", encoding="utf-8")
        (repo / "script.js").write_text("\n", encoding="utf-8")
        (repo / "print.css").write_text("\n", encoding="utf-8")
        self.commit(repo, "Contido inicial", "2026-01-10T12:00:00+01:00")
        return temporary, repo

    def test_relevant_source_updates_the_page_date(self):
        temporary, repo = self.make_repo()
        self.addCleanup(temporary.cleanup)
        (repo / "styles.css").write_text("body { color: green; }\n", encoding="utf-8")
        self.commit(repo, "Axusta o estilo", "2026-02-20T12:00:00+01:00")
        self.assertEqual(page_date.latest_page_change("HEAD", repo).display_date, "20.02.2026")

    def test_configuration_change_does_not_update_the_page_date(self):
        temporary, repo = self.make_repo()
        self.addCleanup(temporary.cleanup)
        (repo / "config.yml").write_text("value: changed\n", encoding="utf-8")
        self.commit(repo, "Cambia a configuración", "2026-03-15T12:00:00+01:00")
        self.assertEqual(page_date.latest_page_change("HEAD", repo).display_date, "10.01.2026")

    def test_generated_commit_is_ignored(self):
        temporary, repo = self.make_repo()
        self.addCleanup(temporary.cleanup)
        index = repo / "index.html"
        index.write_text(index.read_text(encoding="utf-8").replace("10.01.2026", "01.04.2026"), encoding="utf-8")
        self.commit(repo, "Actualiza a data xeral [skip page-date]", "2026-04-01T12:00:00+02:00")
        self.assertEqual(page_date.latest_page_change("HEAD", repo).display_date, "10.01.2026")

    def test_document_updates_visible_and_structured_dates(self):
        change = page_date.Change(0, "2026-05-05T18:30:00+02:00", "abc")
        updated = page_date.update_document(DOCUMENT, change)
        self.assertIn('datetime="2026-05-05">05.05.2026</time>', updated)
        self.assertIn('"dateModified":"2026-05-05T18:30:00+02:00"', updated)

    def test_shallow_history_is_rejected(self):
        temporary, repo = self.make_repo()
        self.addCleanup(temporary.cleanup)
        (repo / "index.html").write_text(DOCUMENT.replace("Web", "Web nova"), encoding="utf-8")
        self.commit(repo, "Segundo cambio", "2026-06-10T12:00:00+02:00")
        shallow_parent = tempfile.TemporaryDirectory()
        self.addCleanup(shallow_parent.cleanup)
        shallow = Path(shallow_parent.name) / "shallow"
        subprocess.run(
            ("git", "clone", "--depth", "1", f"file://{repo}", str(shallow)),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with self.assertRaises(page_date.PageDateError):
            page_date.latest_page_change("HEAD", shallow)


if __name__ == "__main__":
    unittest.main()
