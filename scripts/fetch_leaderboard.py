"""Fetch and parse the public DrivenData GEMS leaderboard into a machine-readable feed.

Standard library only (runs on a bare GitHub-hosted runner without pip installs).

Usage
-----
  python scripts/fetch_leaderboard.py                # fetch live page, write feed
  python scripts/fetch_leaderboard.py --html f.html  # parse a saved page (offline test)
  python scripts/fetch_leaderboard.py --out docs/leaderboard.json --snapshots evidence/leaderboard

Outputs
-------
  docs/leaderboard.json                latest feed (status, fetched_utc, rows, watched accounts)
  evidence/leaderboard/YYYY-MM-DD.json dated snapshot (only when the parse succeeded)

The sandbox this repository is developed in has no route to drivendata.org, so the
network path is exercised by .github/workflows/leaderboard-feed.yml on a GitHub-hosted
runner; the parser is unit-tested offline against a synthetic table in tests/test_round7.py.

Nothing here is authoritative: the page is the source of truth, and every row carries
the URL it was parsed from.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
UA = "12GEMSDOE-leaderboard-feed/1.0 (+https://github.com/buffedlizard55-lab/12GEMSDOE)"

# Accounts whose position we always report, with the (unverified) reason we watch them.
WATCH = {
    "DARD": "leader at last manual check (0.3168, 2026-09-28)",
    "alexoktaba": "#2 at last manual check",
    "HardcoreTechGod": "#3 at last manual check",
    "mzoorob": "#4 at last manual check",
    "joeyfezster": "#5 at last manual check (Phase-1 top-5 cutoff)",
    "GrigorSargsyan": "#6 at last manual check",
    "doegemsDrivendata": "name suggests organizer reference U-Net (0.1847); NOT verified",
    "extradr19": "0.1563 = group ens12 artifact score? ownership NOT verified",
    "SDCF9": "0.1563, same value as extradr19; ownership NOT verified",
    "smashi34": "0.1563, same value as extradr19; ownership NOT verified",
    "wbg1": "0.1461 = 7GEMSDOE README claim; ownership NOT verified",
    "smrtdoog5": "0.1193 = GEMSDOE3 README claim; ownership NOT verified",
}


class TableParser(HTMLParser):
    """Collect every <table> as a list of rows; each cell = (text, hrefs)."""

    def __init__(self):
        super().__init__()
        self.tables, self._table, self._row, self._cell = [], None, None, None
        self._hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell, self._hrefs = [], []
        elif tag == "a" and self._cell is not None:
            href = dict(attrs).get("href")
            if href:
                self._hrefs.append(href)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            self._row.append((text, list(self._hrefs)))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def parse_leaderboard(html: str) -> list[dict]:
    p = TableParser()
    p.feed(html)
    for table in p.tables:
        header = [c[0].lower() for c in table[0]]
        if not any("rank" in h for h in header) or not any("score" in h for h in header):
            continue
        col = {}
        for i, h in enumerate(header):
            if "rank" in h and "rank" not in col:
                col["rank"] = i
            elif "score" in h and "score" not in col:
                col["score"] = i
            elif "submission" in h and "last" in h:
                col["last_submission"] = i
            elif "submission" in h and "submissions" not in col:
                col["submissions"] = i
            elif "name" in h or "team" in h or "user" in h:
                col.setdefault("name", i)
        rows = []
        for r in table[1:]:
            if len(r) <= max(col.values()):
                continue
            try:
                rank = int(re.sub(r"[^0-9]", "", r[col["rank"]][0]))
                score = float(r[col["score"]][0])
            except (ValueError, KeyError):
                continue
            name_cell = r[col["name"]] if "name" in col else ("", [])
            profile = next((h for h in name_cell[1] if "/users/" in h), None)
            name = name_cell[0]
            if profile:
                name = profile.rstrip("/").split("/")[-1] or name
            row = {"rank": rank, "name": name, "display": name_cell[0], "score": score}
            if profile:
                row["profile"] = profile
            if "submissions" in col:
                try:
                    row["submissions"] = int(re.sub(r"[^0-9]", "", r[col["submissions"]][0]))
                except ValueError:
                    pass
            if "last_submission" in col:
                row["last_submission"] = r[col["last_submission"]][0]
            rows.append(row)
        if rows:
            return rows
    return []


def build_feed(rows: list[dict], fetched_utc: str, source: str, status: str, error: str | None = None) -> dict:
    by_name = {r["name"]: r for r in rows}
    watched = {}
    for name, why in WATCH.items():
        r = by_name.get(name)
        watched[name] = {"why": why, "rank": r["rank"] if r else None, "score": r["score"] if r else None,
                         "submissions": r.get("submissions") if r else None}
    return {
        "status": status,
        "error": error,
        "source_url": URL,
        "source": source,
        "fetched_utc": fetched_utc,
        "metric": "public DW-Tversky (DTI), higher is better; scored only on expert-labelled new faults; catalogue pixels masked",
        "n_rows": len(rows),
        "top5_cutoff_score": rows[4]["score"] if len(rows) >= 5 else None,
        "rows": rows,
        "watched": watched,
        "caveat": "Public leaderboard only. Phase-1 prizes are decided on this board; Phase-2 uses an expanded expert-reviewed truth set. Account ownership in `watched` is NOT verified.",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", help="parse a saved HTML file instead of fetching")
    ap.add_argument("--out", default=str(ROOT / "docs/leaderboard.json"))
    ap.add_argument("--snapshots", default=str(ROOT / "evidence/leaderboard"))
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--dump", help="write the raw fetched HTML here (diagnostics; uploaded as a CI artifact)")
    args = ap.parse_args(argv)

    fetched = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    error, html, source = None, "", URL
    if args.html:
        html = Path(args.html).read_text(errors="replace")
        source = f"file:{args.html}"
    else:
        try:
            req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 — we want the message in the feed
            error = f"{type(exc).__name__}: {exc}"

    if args.dump and html:
        Path(args.dump).write_text(html)
    rows = parse_leaderboard(html) if html else []
    status = "ok" if rows else ("fetch-failed" if error else "parse-failed")
    feed = build_feed(rows, fetched, source, status, error)
    if status != "ok" and html:
        # diagnostics so a parse failure can be understood from the committed feed alone
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        feed["diagnostics"] = {
            "html_bytes": len(html),
            "title": re.sub(r"\s+", " ", title.group(1)).strip()[:200] if title else None,
            "n_tables": html.lower().count("<table"),
            "has_leaderboard_word": "leaderboard" in html.lower(),
            "snippet": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))[:400],
        }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if status == "ok":
        out.write_text(json.dumps(feed, indent=2))
        snap_dir = Path(args.snapshots)
        snap_dir.mkdir(parents=True, exist_ok=True)
        (snap_dir / f"{fetched[:10]}.json").write_text(json.dumps(feed, indent=2))
    else:
        # keep the last good feed's rows, but record the failure so the site shows it
        prev = json.loads(out.read_text()) if out.exists() else {}
        prev.update({"status": status, "error": error, "last_attempt_utc": fetched,
                     "diagnostics": feed.get("diagnostics")})
        out.write_text(json.dumps(prev, indent=2))
    print(json.dumps({"status": status, "n_rows": len(rows), "error": error,
                      "top5": [(r["rank"], r["name"], r["score"]) for r in rows[:5]]}, indent=2))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
