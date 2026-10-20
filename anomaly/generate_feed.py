#!/usr/bin/env python3
"""Build the Anomaly podcast feed using the publisher-only anthology engine.

The original 120 publisher identities are preserved for subscribers.
"""
from __future__ import annotations
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CANONICAL = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/"

def main():
    legacy = runpy.run_path(str(HERE / "engine.py"), run_name="anomaly_algorithm")
    engine = legacy["main"].__globals__
    catalog = json.loads((HERE / "catalog.json").read_text(encoding="utf-8"))
    engine["HERE"] = HERE
    engine["CATALOG"] = catalog
    engine["THEMES"] = catalog["themes"]
    engine["ROOT"] = CANONICAL
    original_cover = engine["create_cover"]

    def cover(path):
        original_cover(path)
        from PIL import Image, ImageDraw, ImageFont
        with Image.open(path) as src:
            image = src.convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((75, 1040, 1425, 1420), fill=(18,25,34), radius=20)
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        try:
            big = ImageFont.truetype(font_path, 127)
            small = ImageFont.truetype(font_path, 58)
        except OSError:
            big = small = ImageFont.load_default()
        draw.text((750,1080),"ANOMALY",font=big,anchor="mt",fill=(238,222,187))
        draw.text((750,1270),"STORIES  +  ACTUAL PLAYS",font=small,anchor="mt",fill=(222,179,107))
        image.save(path,format="PNG",optimize=True)

    engine["create_cover"] = cover

    # Pin the 23 individually audited episode swaps to their original slots,
    # preserving the other 97 items, their positions and their GUIDs.
    plan = json.loads((HERE / "replacement-plan.json").read_text(encoding="utf-8"))
    baseline = json.loads((HERE / "episode-baseline-2026-10-20.json").read_text(encoding="utf-8"))["episodes"]
    original_lock = json.loads((HERE / "selection-lock-baseline-2026-10-20.json").read_text(encoding="utf-8"))
    positions = {int(p): record for p, record in plan["replacements"].items()}
    assert len(positions) == 23 and len(baseline) == 120
    assert len({r["episode_key"] for r in positions.values()}) == 23
    themes = list(catalog["themes"])
    for number, record in positions.items():
        assert 1 <= number <= 120
        theme = themes[(number - 1) // 20]
        role = "story" if number % 2 else "actual_play"
        offset = ((number - 1) % 20) // 2
        assert record["number"] == number
        assert record["theme"] == theme and record["role"] == role
        src = next(s for s in catalog["sources"] if s["id"] == record["source"])
        assert role == src["role"] and theme in src["themes"]
        # Idempotent: after first successful publication the slot is already pinned.
        original_lock[theme][role][offset] = record["episode_key"]
    (HERE / "selection-lock.json").write_text(
        json.dumps(original_lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    engine["main"]()

    # Fail the release before publishing if a publisher RSS has changed or a
    # normal pre-existing episode moved. RSS GUIDs are authoritative identities.
    generated = json.loads((HERE / "episodes.json").read_text(encoding="utf-8"))
    import xml.etree.ElementTree as ET
    xml_items = ET.parse(HERE / "feed-v2.xml").findall("./channel/item")
    assert len(generated) == len(xml_items) == 120
    bad = []
    for i, (entry, item, prior) in enumerate(zip(generated, xml_items, baseline), 1):
        guid = item.findtext("guid")
        if i in positions:
            wanted = positions[i]
            wanted_source = next(s for s in catalog["sources"] if s["id"] == wanted["source"])
            if not (entry["title"] == wanted["title"] and
                    entry["publisher"] == wanted_source["name"] and
                    entry["theme"] == wanted["theme"] and entry["role"] == wanted["role"] and
                    guid != prior["guid"]):
                bad.append((i, "Replacement not found", entry["title"]))
        else:
            if not (entry["title"] == prior["title"] and
                    entry["publisher"] == prior["publisher"] and guid == prior["guid"]):
                bad.append((i, "Original changed", entry["title"]))
    if bad:
        raise RuntimeError("Anomaly 23-swap integrity failed: " + repr(bad))
    print("PASS 23 reviewed replacements, 97 original GUIDs unchanged, 120 entries", flush=True)

    for name in ("feed-v2.xml","feed.xml"):
        path=HERE/name
        raw=path.read_text(encoding="utf-8")
        raw=raw.replace("Magudonya/Anomaly themes", "Anomaly campaign themes")
        raw=raw.replace("Magudonya independent listening catalog", "Anomaly independent listening catalog")
        raw=raw.replace("NOT as Magudonya canon", "NOT as Anomaly canon")
        # Existing episode GUIDs are intentionally kept under their original
        # URN namespace to prevent a 120-episode duplicate import.
        assert raw.count("urn:magudonya:1:")==120  # Historical podcast IDs only
        assert "/magudonya/" not in raw.lower()
        assert "Veyrun" not in raw
        assert "/anomaly/" in raw
        path.write_text(raw,encoding="utf-8")
    index=HERE/"episodes.md"
    print("Anomaly RSS validated: 120 stable episode GUIDs, corrected title and metadata",flush=True)

if __name__=="__main__":
    main()
