#!/usr/bin/env python3
"""
fetch_epg.py

Fetches ONE XMLTV source (plain .xml or gzipped .xml.gz) at a time, parses
channels + programmes, and writes data/epg_data.json containing -- for every
channel -- the ID, display name, the CURRENTLY AIRING programme, and the
NEXT programme only. Everything else (the full multi-day guide) is discarded
before writing, which is what keeps the output file small.

Every run fully OVERWRITES data/epg_data.json. There is no accumulation of
old runs and no merging across past fetches -- each run starts clean from
the freshly fetched source.

No CORS involved anywhere -- this runs server-side (GitHub Actions runner,
or your own machine), so it's a plain HTTP request, not a browser fetch.

Usage:
    python fetch_epg.py --url "https://example.com/guide.xml.gz" --label "US Locals"
"""

import argparse
import gzip
import io
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET

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
            tz = timezone(sign * timedelta(hours=hours, minutes=minutes))
            return dt.replace(tzinfo=tz)
        else:
            dt = datetime.strptime(value[:14], "%Y%m%d%H%M%S")
            return dt.replace(tzinfo=timezone.utc)
    except (ValueError, IndexError):
        return None


def parse_xmltv_streaming(xml_bytes: bytes, now: datetime):
    """
    Memory-conscious parse: iterparse over the XML so we never hold the full
    multi-day guide in memory at once, and immediately reduce each channel's
    programme list down to just "current" and "next" as we go, discarding
    everything else (past programmes, and anything beyond next-up) right away.

    Returns:
        channels: dict id -> display name
        now_next: dict id -> {"current": {...} | None, "next": {...} | None}
    """
    channels = {}
    now_next = {}

    context = ET.iterparse(io.BytesIO(xml_bytes), events=("end",))
    for event, elem in context:
        if elem.tag == "channel":
            ch_id = elem.get("id")
            if ch_id:
                dn = elem.find("display-name")
                channels[ch_id] = dn.text.strip() if dn is not None and dn.text else ch_id
            elem.clear()

        elif elem.tag == "programme":
            ch_id = elem.get("channel")
            start = parse_xmltv_time(elem.get("start"))
            stop = parse_xmltv_time(elem.get("stop"))
            if ch_id and start and stop:
                title_el = elem.find("title")
                desc_el = elem.find("desc")
                title = title_el.text.strip() if title_el is not None and title_el.text else "(no title)"
                desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
                entry = {
                    "start": start.isoformat(),
                    "stop": stop.isoformat(),
                    "title": title,
                    "desc": desc,
                }
                slot = now_next.setdefault(ch_id, {"current": None, "next": None,
                                                     "_next_start": None})

                if start <= now < stop:
                    slot["current"] = entry
                elif start > now:
                    if slot["_next_start"] is None or start < slot["_next_start"]:
                        slot["next"] = entry
                        slot["_next_start"] = start
                # Past programmes (stop <= now) are simply never stored.

            # Free memory for this element immediately -- this is what keeps
            # peak memory (and therefore the eventual JSON) small even for
            # multi-day, hundreds-of-channels guides.
            elem.clear()

    for ch_id in now_next:
        now_next[ch_id].pop("_next_start", None)

    for ch_id in now_next:
        channels.setdefault(ch_id, ch_id)

    return channels, now_next


def build_source_entry(key: str, label: str, url: str):
    print(f"[{key}] fetching {url}", file=sys.stderr)
    try:
        raw = fetch_bytes(url)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[{key}] FAILED to fetch: {e}", file=sys.stderr)
        return {"key": key, "label": label, "url": url, "error": str(e), "channels": {}}

    try:
        xml_bytes = maybe_gunzip(raw)
        now = datetime.now(timezone.utc)
        channels, now_next = parse_xmltv_streaming(xml_bytes, now)
    except ET.ParseError as e:
        print(f"[{key}] FAILED to parse: {e}", file=sys.stderr)
        return {"key": key, "label": label, "url": url, "error": f"XML parse error: {e}", "channels": {}}

    out_channels = {}
    for ch_id, name in channels.items():
        slot = now_next.get(ch_id, {"current": None, "next": None})
        out_channels[ch_id] = {
            "name": name,
            "current": slot.get("current"),
            "next": slot.get("next"),
        }

    print(f"[{key}] OK -- {len(out_channels)} channels (now/next only)", file=sys.stderr)
    return {"key": key, "label": label, "url": url, "error": None, "channels": out_channels}


def main():
    parser = argparse.ArgumentParser(description="Fetch one XMLTV source, keep only now+next per channel.")
    parser.add_argument("--url", required=True, help="XMLTV URL (.xml or .xml.gz).")
    parser.add_argument("--label", default="EPG Source", help="Label to show on the page.")
    parser.add_argument("--out", default=OUTPUT_PATH, help="Output JSON path.")
    args = parser.parse_args()

    result = build_source_entry("source", args.label, args.url)

    # Always a clean, full overwrite -- no merging with any previous run,
    # no leftover channels or programmes from earlier fetches.
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": result,
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(args.out) / 1024
    print(f"Wrote {args.out} -- {len(result['channels'])} channels, {size_kb:.1f} KB.", file=sys.stderr)


if __name__ == "__main__":
    main()
