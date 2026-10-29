#!/usr/bin/env python3
"""Actualiza a data xeral da web a partir do historial de Git."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Mapa explícito das fontes que constitúen a páxina publicada. Os cambios en
# workflows, probas, dependencias ou configuración quedan fóra deste cálculo.
PAGE_SOURCES = (
    "index.html",
    "styles.css",
    "script.js",
    "print.css",
)

# Os commits creados polo propio workflow levan esta marca para evitar que a
# data xerada se considere unha nova actualización da web.
GENERATED_COMMIT_MARKER = "[skip page-date]"


class PageDateError(RuntimeError):
    pass


@dataclass(frozen=True)
class Change:
    timestamp: int
    iso_datetime: str
    commit: str

    @property
    def iso_date(self) -> str:
        return self.iso_datetime[:10]

    @property
    def display_date(self) -> str:
        return datetime.strptime(self.iso_date, "%Y-%m-%d").strftime("%d.%m.%Y")


def git(*args: str, cwd: Path = ROOT, allow_failure: bool = False) -> str | None:
    result = subprocess.run(
        ("git", *args),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        if allow_failure:
            return None
        message = result.stderr.strip() or "Erro descoñecido de Git."
        raise PageDateError(message)
    return result.stdout


def require_full_history(cwd: Path = ROOT) -> None:
    shallow = (git("rev-parse", "--is-shallow-repository", cwd=cwd) or "").strip()
    if shallow == "true":
        raise PageDateError(
            "O historial de Git é superficial. Executa o checkout con fetch-depth: 0 "
            "antes de calcular a data. A data existente conservarase sen cambios."
        )


def latest_page_change(ref: str, cwd: Path = ROOT) -> Change:
    require_full_history(cwd)
    output = git(
        "log",
        "--format=%H%x00%ct%x00%cI%x00%s",
        ref,
        "--",
        *PAGE_SOURCES,
        cwd=cwd,
    ) or ""
    for line in output.splitlines():
        commit, timestamp, iso_datetime, subject = line.split("\x00", 3)
        if GENERATED_COMMIT_MARKER in subject:
            continue
        return Change(int(timestamp), iso_datetime, commit)
    raise PageDateError(
        "Non foi posible localizar no historial un cambio nas fontes da páxina. "
        "A data existente conservarase sen cambios."
    )


def marker_block(change: Change) -> str:
    return (
        "<!-- page-updated:start -->\n"
        '<p class="page-updated" data-page-updated>'
        'ÚLTIMA ACTUALIZACIÓN: '
        f'<time datetime="{change.iso_date}">{change.display_date}</time></p>\n'
        "<!-- page-updated:end -->"
    )


def update_document(document: str, change: Change) -> str:
    marker_pattern = re.compile(
        r"<!--\s*page-updated:start\s*-->.*?<!--\s*page-updated:end\s*-->",
        re.IGNORECASE | re.DOTALL,
    )
    updated, marker_count = marker_pattern.subn(marker_block(change), document, count=1)
    if marker_count != 1:
        raise PageDateError("Falta o marcador da data xeral no pé da páxina.")

    structured_pattern = re.compile(r'("dateModified"\s*:\s*")[^"]+(")')
    structured_value = change.iso_datetime
    updated, structured_count = structured_pattern.subn(
        rf"\g<1>{structured_value}\g<2>", updated, count=1
    )
    if structured_count != 1:
        raise PageDateError("Falta dateModified nos datos estruturados da páxina.")
    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="HEAD", help="Referencia de Git que se analiza.")
    parser.add_argument("--write", action="store_true", help="Actualiza index.html.")
    parser.add_argument(
        "--check", action="store_true", help="Comproba que index.html xa está actualizado."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        change = latest_page_change(args.ref)
        document_path = ROOT / "index.html"
        current = document_path.read_text(encoding="utf-8")
        expected = update_document(current, change)

        print("PÁXINA\tDATA\tCOMMIT")
        print(f"Web xeral\t{change.display_date}\t{change.commit[:10]}")

        if args.check and current != expected:
            print("A data de index.html está desactualizada.", file=sys.stderr)
            return 1
        if args.write and current != expected:
            document_path.write_text(expected, encoding="utf-8")
    except PageDateError as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
