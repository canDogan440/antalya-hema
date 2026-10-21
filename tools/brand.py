"""Build brand images from the club banner.

Usage: python tools/brand.py <banner.jpg>

Writes into site/img/brand/:
  banner.webp / banner.png   banner with the black surround made transparent
  emblem-512.png, emblem-192.png, apple-touch-icon.png, favicon-32.png, favicon.ico
  og-image.jpg               1200x630 social preview
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "img", "brand")
TEAL = (16, 63, 66)
GOLD = (224, 194, 122)
CREAM = (243, 236, 220)
GRIFFIN_BOX = (60, 590, 770, 1300)  # square crop around the griffin


def transparent_banner(src):
    im = src.convert("RGB")
    w, h = im.size
    key = (255, 0, 255)
    work = im.copy()
    seeds = [(x, 0) for x in range(0, w, 6)] + [(x, h - 1) for x in range(0, w, 6)]
    seeds += [(0, y) for y in range(0, h, 6)] + [(w - 1, y) for y in range(0, h, 6)]
    for s in seeds:
        r, g, b = work.getpixel(s)
        if r + g + b < 90:
            ImageDraw.floodfill(work, s, key, thresh=60)
    mask = Image.new("L", (w, h), 255)
    mp, wp = mask.load(), work.load()
    for y in range(h):
        for x in range(w):
            if wp[x, y] == key:
                mp[x, y] = 0
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out.crop(out.getbbox())


def emblem(src, size):
    crop = src.convert("RGB").crop(GRIFFIN_BOX).resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(crop, (0, 0), m)
    ring = ImageDraw.Draw(out)
    wdt = max(2, size // 40)
    ring.ellipse((wdt // 2, wdt // 2, size - 1 - wdt // 2, size - 1 - wdt // 2), outline=GOLD + (255,), width=wdt)
    return out


def font(names, size):
    for n in names:
        p = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", n)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def og_image(banner):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), TEAL)
    d = ImageDraw.Draw(im)
    for i in range(0, W, 4):  # subtle vertical sheen
        d.line([(i, 0), (i, H)], fill=(16 + (i % 40) // 10, 63, 66))
    b = banner.copy()
    b.thumbnail((260, 590), Image.LANCZOS)
    im.paste(b, (W - b.width - 70, (H - b.height) // 2), b)
    serif_b = font(["georgiab.ttf", "timesbd.ttf"], 74)
    serif = font(["georgia.ttf", "times.ttf"], 38)
    small = font(["georgia.ttf", "times.ttf"], 28)
    d.text((80, 150), "Lycian Fighters", font=serif_b, fill=GOLD)
    d.text((80, 250), "Antalya HEMA Kulübü", font=serif, fill=CREAM)
    d.text((80, 300), "Tarihi Avrupa Dövüş Sanatları", font=serif, fill=CREAM)
    d.line([(80, 380), (560, 380)], fill=GOLD, width=2)
    d.text((80, 405), "Uzun kılıç · Meyer · Liechtenauer", font=small, fill=GOLD)
    d.text((80, 450), "4x4 Sport Center Uncalı · Antalya", font=small, fill=CREAM)
    return im


def main(src_path):
    os.makedirs(OUT, exist_ok=True)
    src = Image.open(src_path)
    banner = transparent_banner(src)
    banner.save(os.path.join(OUT, "banner.png"), optimize=True)
    small = banner.copy()
    small.thumbnail((480, 1180), Image.LANCZOS)
    small.save(os.path.join(OUT, "banner.webp"), "WEBP", quality=86, method=6)
    print("banner", banner.size, "->", small.size)

    e = emblem(src, 512)
    e.save(os.path.join(OUT, "emblem-512.png"), optimize=True)
    e.resize((192, 192), Image.LANCZOS).save(os.path.join(OUT, "emblem-192.png"), optimize=True)
    e.resize((96, 96), Image.LANCZOS).save(os.path.join(OUT, "emblem-96.webp"), "WEBP", quality=90)
    touch = Image.new("RGB", (180, 180), TEAL)
    touch.paste(e.resize((168, 168), Image.LANCZOS), (6, 6), e.resize((168, 168), Image.LANCZOS))
    touch.save(os.path.join(OUT, "apple-touch-icon.png"), optimize=True)
    e.resize((32, 32), Image.LANCZOS).save(os.path.join(OUT, "favicon-32.png"), optimize=True)
    e.save(os.path.join(ROOT, "site", "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

    og_image(banner).save(os.path.join(OUT, "og-image.jpg"), quality=86, optimize=True)
    print("brand images written to", OUT)


if __name__ == "__main__":
    main(sys.argv[1])
