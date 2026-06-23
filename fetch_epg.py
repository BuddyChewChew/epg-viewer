#!/usr/bin/env python3
"""
fetch_epg.py

Fetches one or more XMLTV sources (plain .xml or gzipped .xml.gz), parses
channels + programmes, and writes a single epg_data.json containing, for
every channel: id, display name, current programme, and next programme.

No CORS involved anywhere -- this runs server-side (GitHub Actions runner
or your own machine), so it's a plain HTTP request, not a browser fetch.

Usage:
    python fetch_epg.py
        Fetches every URL in DEFAULT_SOURCES (below) and writes data/epg_data.json.

    python fetch_epg.py --url "https://example.com/some_guide.xml.gz" --label "Spot Check"
        Fetches just that one URL instead of the defaults, still writes
        data/epg_data.json (used by the manual workflow_dispatch run).

    python fetch_epg.py --url URL1 --url URL2 --label "A" --label "B"
        Multiple ad-hoc URLs, paired by position with --label.
"""

import argparse
import gzip
import io
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Default sources fetched on every scheduled (automatic) run.
# Add/remove entries here for the baseline dataset. Each needs a short
# "key" (used as an internal id / tab key) and a "label" (shown on the page).
# ---------------------------------------------------------------------------
DEFAULT_SOURCES = [
    {
        "key": "locals",
        "label": "US Locals",
        "url": "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz",
    },
    {
        "key": "us1",
        "label": "US1",
        "url": "https://epgshare01.online/epgshare01/epg_ripper_US1.xml.gz",
    },
    {
        "key": "us2",
        "label": "US2",
        "url": "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
    },
]

OUTPUT_PATH = "data/epg_data.json"
REQUEST_TIMEOUT = 60
USER_AGENT = "Mozilla/5.0 (compatible; epg-fetch-script/1.0)"


def fetch_bytes(url: str) -> bytes:
    """Plain HTTP GET. Runs server-side -- no CORS concept applies here at all."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return resp.read()


def maybe_gunzip(raw: bytes) -> bytes:
    """Detect gzip magic bytes and decompress if needed; otherwise return as-is."""
    if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
            return gz.read()
    return raw


def parse_xmltv_time(value: str):
    """Parse XMLTV timestamps like '20260623183000 -0400' into aware datetimes."""
    if not value:
        return None
    value = value.strip()
    try:
        if " " in value:
            dt_part, offset = value.split(" ", 1)
            dt = datetime.strptime(dt_part, "%Y%m%d%H%M%S")
            sign = 1 if offset[0] == "+" else -1
            hours = int(offset[1:3])
            minutes = int(offset[3:5])
            from datetime import timedelta
            tz = timezone(sign * timedelta(hours=hours, minutes=minutes))
            return dt.replace(tzinfo=tz)
        else:
            dt = datetime.strptime(value[:14], "%Y%m%d%H%M%S")
            return dt.replace(tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def parse_xmltv(xml_bytes: bytes):
    """
    Returns:
        channels: dict id -> display name
        programmes: dict id -> sorted list of {start_iso, stop_iso, title, desc}
    """
    channels = {}
    programmes = {}

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise ValueError(f"XML parse error: {e}")

    for ch in root.findall("channel"):
        ch_id = ch.get("id")
        if not ch_id:
            continue
        dn = ch.find("display-name")
        channels[ch_id] = dn.text.strip() if dn is not None and dn.text else ch_id

    for p in root.findall("programme"):
        ch_id = p.get("channel")
        start = parse_xmltv_time(p.get("start"))
        stop = parse_xmltv_time(p.get("stop"))
        if not ch_id or not start or not stop:
            continue
        title_el = p.find("title")
        desc_el = p.find("desc")
        title = title_el.text.strip() if title_el is not None and title_el.text else "(no title)"
        desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        programmes.setdefault(ch_id, []).append({
            "start": start.isoformat(),
            "stop": stop.isoformat(),
            "title": title,
            "desc": desc,
        })

    for ch_id in programmes:
        programmes[ch_id].sort(key=lambda p: p["start"])

    # Fall back to using the channel id as its own name if <channel> tags
    # were sparse/missing but programmes reference it.
    for ch_id in programmes:
        channels.setdefault(ch_id, ch_id)

    return channels, programmes


def build_source_entry(key: str, label: str, url: str):
    print(f"[{key}] fetching {url}", file=sys.stderr)
    try:
        raw = fetch_bytes(url)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[{key}] FAILED to fetch: {e}", file=sys.stderr)
        return {"key": key, "label": label, "url": url, "error": str(e),
                "channels": {}, "programmes": {}}

    try:
        xml_bytes = maybe_gunzip(raw)
        channels, programmes = parse_xmltv(xml_bytes)
    except ValueError as e:
        print(f"[{key}] FAILED to parse: {e}", file=sys.stderr)
        return {"key": key, "label": label, "url": url, "error": str(e),
                "channels": {}, "programmes": {}}

    print(f"[{key}] OK -- {len(channels)} channels, {len(programmes)} with listings", file=sys.stderr)
    return {
        "key": key,
        "label": label,
        "url": url,
        "error": None,
        "channels": channels,
        "programmes": programmes,
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch and parse XMLTV EPG sources into JSON.")
    parser.add_argument("--url", action="append", default=[], help="Ad-hoc XMLTV URL (repeatable).")
    parser.add_argument("--label", action="append", default=[], help="Label paired by position with --url.")
    parser.add_argument("--out", default=OUTPUT_PATH, help="Output JSON path.")
    args = parser.parse_args()

    if args.url:
        sources = []
        for i, url in enumerate(args.url):
            label = args.label[i] if i < len(args.label) else f"Custom {i+1}"
            key = f"custom{i+1}"
            sources.append({"key": key, "label": label, "url": url})
        print(f"Running with {len(sources)} ad-hoc source(s) (manual run).", file=sys.stderr)
    else:
        sources = DEFAULT_SOURCES
        print(f"Running with {len(sources)} default source(s) (scheduled run).", file=sys.stderr)

    results = [build_source_entry(s["key"], s["label"], s["url"]) for s in sources]

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": results,
    }

    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    total_channels = sum(len(r["channels"]) for r in results)
    print(f"Wrote {args.out} -- {len(results)} source(s), {total_channels} total channels.", file=sys.stderr)


if __name__ == "__main__":
    main()
