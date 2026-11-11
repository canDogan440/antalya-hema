"""Generate the Fiore atlas fragments (src/atlas/fiore.tr.html, fiore.en.html).

Usage: python tools/fiore.py
Reads src/atlas/fiore_content.py and src/atlas/fiore.plays.json. The output has
the same structure as the other atlas fragments, so build.py can wrap it.
"""
import html, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "atlas"))
import fiore_content as C

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
PAGE = {"tr": "s.", "en": "p."}


def esc(s):
    return html.escape(s, quote=True)


def expand(ranges):
    out = []
    for a, b in ranges:
        out.extend(range(a, b + 1))
    return out


def card(p, lang, cap, cat_name):
    meta = f"Getty {p['ref']} · {PAGE[lang]} {p['page']}" if p["ref"] else f"{PAGE[lang]} {p['page']}"
    return (f'<figure class="card" tabindex="0" data-cap="{esc(cap)}" data-meta="{esc(cat_name)} · {esc(meta)}">'
            f'<img loading="lazy" alt="{esc(cap)}" src="{p["n"]:03d}.webp" width="{p["w"]}" height="{p["h"]}">'
            f'<figcaption><span class="cap">{esc(cap)}</span><span class="meta">{esc(meta)}</span></figcaption></figure>')


def lore(items):
    out = []
    for it in items:
        if isinstance(it, tuple):
            out.append(f"<p><b>{esc(it[0])}</b> {esc(it[1])}</p>")
        else:
            out.append(f'<p class="verse">{esc(it)}</p>')
    return '<div class="lore">' + "".join(out) + "</div>"


def build(lang, plays):
    m = C.MAST[lang]
    idx = 0 if lang == "tr" else 1
    groups_html, toc, chips = [], [], [f'<button class="chip on" data-f="all">{esc(m["all"])} <b>{len(plays)}</b></button>']
    ncat = 0
    for gi, g in enumerate(C.GROUPS):
        gcount = sum(len(expand(c["imgs"])) for c in g["cats"])
        chips.append(f'<button class="chip" data-f="{gi}">{esc(g[lang])} <b>{gcount}</b></button>')
        cats_html = []
        for c in g["cats"]:
            ncat += 1
            title, de, desc = c[lang]
            nums = expand(c["imgs"])
            toc.append(f'<a href="#{c["id"]}" data-group="{gi}">{esc(title)}<i>{len(nums)}</i></a>')
            entries = c.get("entries", {})
            parts = []
            if entries:
                arts = []
                for n in nums:
                    if n not in entries:
                        continue
                    h3, txt = entries[n][idx]
                    arts.append(f'<article class="entry">{card(plays[n], lang, h3 + " — " + plays[n]["title"], title)}'
                                f'<div class="txt"><h3>{esc(h3)}</h3><p class="where">{esc(plays[n]["title"])}</p>'
                                f'<p>{esc(txt)}</p><span class="src">Getty {esc(plays[n]["ref"])} · {PAGE[lang]} {plays[n]["page"]}</span></div></article>')
                parts.append('<div class="entries" data-gal>' + "".join(arts) + "</div>")
            rest = [n for n in nums if n not in entries]
            if rest:
                parts.append('<div class="grid" data-gal>' + "".join(card(plays[n], lang, plays[n]["title"], title) for n in rest) + "</div>")
            cats_html.append(
                f'<section class="cat" id="{c["id"]}" data-group="{gi}"><header class="cathead">'
                f'<h3>{esc(title)} <span class="de">{esc(de)}</span></h3><p>{esc(desc)}</p><span class="count">{len(nums)}</span></header>'
                f'{lore(c["lore_" + lang])}{"".join(parts)}</section>')
        groups_html.append(
            f'<div class="group" data-group="{gi}" id="g{gi}"><h2><span class="gnum">{ROMAN[gi]}</span>{esc(g[lang])} '
            f'<small>{gcount} {esc(m["count"])}</small></h2>{"".join(cats_html)}</div>')

    intro_title, intro = C.INTRO[lang]
    intro_html = ('<section class="intro"><h2>' + esc(intro_title) + '</h2><div class="cols">'
                  + "".join(f"<p><b>{esc(b)}</b> {esc(t)}</p>" for b, t in intro) + "</div></section>")
    stats = "".join(f"<span><b>{esc(a)}</b>{esc(b)}</span>" for a, b in
                    [(str(len(plays)), m["stats"][0][1]), (str(ncat), m["stats"][1][1]), (str(len(C.GROUPS)), m["stats"][2][1])])
    return (f'<div class="wrap mast">\n  <div class="eyebrow">{esc(m["eyebrow"])}</div>\n  <h1>Fiore</h1>\n'
            f'  <p class="lede">{esc(m["lede"])}</p>\n  <div class="stats">{stats}</div>\n'
            f'  <p class="src-note">{esc(m["source"])}</p>\n</div>\n'
            f'<nav class="bar" aria-label="{esc(m["filter"])}"><div class="wrap">{"".join(chips)}</div></nav>\n'
            f'<div class="wrap">\n  <div class="toc">{"".join(toc)}</div>{intro_html}\n  {"".join(groups_html)}\n</div>\n')


def main():
    plays = {p["n"]: p for p in json.load(open(os.path.join(ROOT, "src", "atlas", "fiore.plays.json"), encoding="utf-8"))}
    used = []
    for g in C.GROUPS:
        for c in g["cats"]:
            used += expand(c["imgs"])
    missing = sorted(set(plays) - set(used))
    dup = sorted({n for n in used if used.count(n) > 1})
    assert not missing and not dup, (missing, dup)
    for lang in ("tr", "en"):
        out = os.path.join(ROOT, "src", "atlas", f"fiore.{lang}.html")
        open(out, "w", encoding="utf-8", newline="\n").write(build(lang, plays))
        print("wrote", out)


if __name__ == "__main__":
    main()
