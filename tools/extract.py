"""One-off import of the two "Çizim Atlası" HTML files.

Usage: python tools/extract.py <meyer.html> <liechtenauer.html>

Writes:
  src/atlas/<name>.tr.html        body fragment (mast + filter bar + content)
  src/atlas/<name>.segments.txt   numbered Turkish parts to translate
  site/img/<name>/NNN.webp        full image, plus thumbs/NNN.webp
"""
import base64, io, os, re, sys
from bs4 import BeautifulSoup, NavigableString
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from i18n import parts_of, TRANSLATABLE_ATTRS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THUMB_W = 520


def save_images(html, name):
    out = os.path.join(ROOT, "site", "img", name)
    os.makedirs(os.path.join(out, "thumbs"), exist_ok=True)
    n = [0]

    def rep(m):
        n[0] += 1
        fn = f"{n[0]:03d}"
        im = Image.open(io.BytesIO(base64.b64decode(m.group(1)))).convert("RGB")
        if im.width > 1400:
            im = im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS)
        im.save(os.path.join(out, fn + ".webp"), "WEBP", quality=80, method=6)
        th = im.copy()
        if th.width > THUMB_W:
            th = th.resize((THUMB_W, round(th.height * THUMB_W / th.width)), Image.LANCZOS)
        th.save(os.path.join(out, "thumbs", fn + ".webp"), "WEBP", quality=72, method=6)
        return f"{fn}.webp\" width=\"{th.width}\" height=\"{th.height}"

    html = re.sub(r"data:image/jpeg;base64,([A-Za-z0-9+/=]+)", rep, html)
    return html, n[0]


def main(meyer, lich):
    os.makedirs(os.path.join(ROOT, "src", "atlas"), exist_ok=True)
    for name, path in (("meyer", meyer), ("liechtenauer", lich)):
        raw = open(path, encoding="utf-8").read()
        raw, count = save_images(raw, name)
        start = raw.index('<div class="wrap mast">')
        end = raw.index('<div class="lb"')
        frag = raw[start:end].strip()
        open(os.path.join(ROOT, "src", "atlas", f"{name}.tr.html"), "w", encoding="utf-8").write(frag + "\n")

        soup = BeautifulSoup(frag, "html.parser")
        seen = []
        for node in soup.find_all(string=True):
            if isinstance(node, NavigableString):
                for p in parts_of(str(node)):
                    if p not in seen:
                        seen.append(p)
        for tag in soup.find_all(True):
            for a in TRANSLATABLE_ATTRS:
                if tag.has_attr(a):
                    for p in parts_of(tag[a]):
                        if p not in seen:
                            seen.append(p)
        with open(os.path.join(ROOT, "src", "atlas", f"{name}.segments.txt"), "w", encoding="utf-8") as f:
            for i, s in enumerate(seen, 1):
                f.write(f"{i}|{s}\n")
        print(name, "images:", count, "segments:", len(seen))


if __name__ == "__main__":
    main(*sys.argv[1:3])
