#!/usr/bin/env python3
"""Generate original, non-branded 2000px podcast art for the independent RPG index."""
from pathlib import Path
import math
import random
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SIZE = 2000
rng = random.Random(20261011)
im = Image.new("RGB", (SIZE, SIZE), "#090e25")
pix = im.load()
for y in range(SIZE):
    for x in range(SIZE):
        glow = max(0, 1.0-math.hypot((x-1500)*0.8, (y-490)*1.25)/1850)
        b = int(25+45*glow+20*y/SIZE)
        pix[x,y] = (int(8+14*glow), int(16+34*glow), b)
d = ImageDraw.Draw(im)
for i in range(200):
    x = rng.randint(70,SIZE-70)
    y = rng.randint(60,SIZE-80)
    rad = rng.choice([1,2,3,3,4])
    tone = rng.randint(105,235)
    d.ellipse((x-rad,y-rad,x+rad,y+rad), fill=(tone,tone, min(255,tone+15)))
for j in range(8):
    inset=78+j*5
    d.rounded_rectangle((inset,inset,SIZE-inset,SIZE-inset), radius=80,
                         outline=(28+j*2,65+j*3,104+j*3),width=2)
d.arc((200,170,1820,1790),15,132,fill="#40acc6",width=14)
d.arc((360,250,1680,1550),194,305,fill="#bbd4dc",width=8)

def font(px,bold=True):
    paths=[
      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
      "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p,px)
    raise RuntimeError("Missing system TTF font")

def centered(label,y,px,color,bold=True):
    f=font(px,bold)
    bbox=d.textbbox((0,0),label,font=f,stroke_width=0)
    w=bbox[2]-bbox[0]
    d.text(((SIZE-w)//2,y),label,font=f,fill=color)

centered("STAR WARS",540,230,"#eef7ff")
centered("RPG",820,320,"#69d2e6")
d.rounded_rectangle((430,1180,1570,1191),radius=4,fill="#93b7d1")
centered("ACTUAL PLAY",1270,120,"#f0f7ff")
centered("CURATED PODCASTS",1450,66,"#cbd6e9")
centered("FFG  /  D6",1575,80,"#69d2e6")
centered("INDEPENDENT LISTENING COLLECTION",1810,32,"#b5c6e0")
dst=HERE/"cover.png"
im.save(dst,format="PNG",optimize=True)
print(f"Created {dst}: {im.size}, {dst.stat().st_size} bytes")
