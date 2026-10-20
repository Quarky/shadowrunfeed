#!/usr/bin/env python3
"""Build the Anomaly podcast feed using the publisher-only anthology engine.

The former Magudonya path is retained for existing subscribers; the published
Anomaly feed does not use the authors' city as a setting reference.
"""
from __future__ import annotations
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CANONICAL = "https://cdn.jsdelivr.net/gh/Quarky/shadowrunfeed@main/anomaly/"

def main():
    legacy = runpy.run_path(str(REPO / "magudonya" / "generate_feed.py"), run_name="anomaly_algorithm")
    engine = legacy["main"].__globals__
    catalog = json.loads((HERE / "catalog.json").read_text(encoding="utf-8"))
    engine["HERE"] = HERE
    engine["CATALOG"] = catalog
    engine["THEMES"] = catalog["themes"]
    engine["ROOT"] = CANONICAL
    engine["THEME_TERMS"]["communities"] = engine["THEME_TERMS"].pop("reach")
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
    engine["main"]()

    for name in ("feed-v2.xml","feed.xml"):
        path=HERE/name
        raw=path.read_text(encoding="utf-8")
        raw=raw.replace("Magudonya/Anomaly themes", "Anomaly campaign themes")
        raw=raw.replace("https://github.com/Quarky/shadowrunfeed/tree/main/magudonya", "https://github.com/Quarky/shadowrunfeed/tree/main/anomaly")
        raw=raw.replace("Magudonya independent listening catalog", "Anomaly independent listening catalog")
        raw=raw.replace("NOT as Magudonya canon", "NOT as Anomaly canon")
        # Existing episode GUIDs are intentionally kept under their original
        # URN namespace to prevent a 120-episode duplicate import.
        assert raw.count("urn:magudonya:1:")==120
        assert "Veyrun" not in raw
        assert "/anomaly/" in raw
        path.write_text(raw,encoding="utf-8")
    index=HERE/"episodes.md"
    index.write_text(index.read_text(encoding="utf-8").replace("# Magudonya —", "# Anomaly —"),encoding="utf-8")
    print("Anomaly RSS validated: 120 stable episode GUIDs, corrected title and metadata",flush=True)

if __name__=="__main__":
    main()
