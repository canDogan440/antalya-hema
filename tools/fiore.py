"""Generate the Fiore atlas fragments (src/atlas/fiore.tr.html, fiore.en.html).

Usage: python tools/fiore.py
Reads src/atlas/fiore_content.py and src/atlas/fiore.plays.json. The output has
the same structure as the other atlas fragments, so build.py can wrap it.
"""
import glob, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "atlas"))
import fiore_content as C

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
PAGE = {"tr": "s.", "en": "p."}
WIKTENAUER = "https://wiktenauer.com/wiki/Fiore_de%27i_Liberi"
SOURCE_HTML = {
    "tr": ('Görseller: J. Paul Getty Museum, Ms. Ludwig XV 13 (Open Content Program). Türkçe metin: Colin Hatcher\'ın Getty çevirisinden '
           '(<a href="{w}" rel="noopener" target="_blank">Wiktenauer</a>, “The Flower of Battle” derlemesi, 2016) Lycian Fighters tarafından çevrilmiştir; '
           'kaynak gibi <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.tr" rel="license noopener" target="_blank">CC BY-NC-SA 4.0</a> lisansıyla paylaşılır. '
           'Köşeli parantezli notlar derleme editörlerinindir.'),
    "en": ('Images: J. Paul Getty Museum, Ms. Ludwig XV 13 (Open Content Program). Category summaries are our own. The full English translation of every play '
           '(Getty translation by Colin Hatcher, Morgan by Michael Chidester) is in the <a href="{w}" rel="noopener" target="_blank">Wiktenauer</a> '
           '“The Flower of Battle” compilation (2016), licensed <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" rel="license noopener" target="_blank">CC BY-NC-SA 4.0</a>; '
           'the Turkish page carries our translation of it.'),
}
ORD = {"First": "Birinci", "Second": "İkinci", "Third": "Üçüncü", "Fourth": "Dördüncü", "Fifth": "Beşinci", "Sixth": "Altıncı",
       "Seventh": "Yedinci", "Eighth": "Sekizinci", "Ninth": "Dokuzuncu", "Tenth": "Onuncu", "Eleventh": "On birinci",
       "Twelfth": "On ikinci", "Thirteenth": "On üçüncü"}
O = "(" + "|".join(ORD) + ")"
TITLE_RULES = [
    (rf"^{O} Scholar of the {O} Remedy(.*)$", lambda m: f"{ORD[m[2]]} Remedy'nin {ORD[m[1]].lower()} scholar'ı{m[3]}"),
    (rf"^{O} Scholar of the {O} Counter(.*)$", lambda m: f"{ORD[m[2]]} counter'ın {ORD[m[1]].lower()} scholar'ı{m[3]}"),
    (rf"^{O} Scholar of the Remedy$", lambda m: f"Remedy'nin {ORD[m[1]].lower()} scholar'ı"),
    (rf"^{O} Scholar of the {O} Three Remedies$", lambda m: f"{ORD[m[2]]} üç remedy'nin scholar'ı"),
    (r"^Scholar of the (First|Second) Three Remedies$", lambda m: f"{'İlk' if m[1] == 'First' else 'İkinci'} üç remedy'nin scholar'ı"),
    (rf"^{O} Counter to the {O} Remedy$", lambda m: f"{ORD[m[2]]} Remedy'ye {ORD[m[1]].lower()} counter"),
    (rf"^{O} Counter to the {O} Scholar$", lambda m: f"{ORD[m[2]]} scholar'a {ORD[m[1]].lower()} counter"),
    (rf"^{O} Counter to the Remedy(.*)$", lambda m: f"Remedy'ye {ORD[m[1]].lower()} counter{m[2]}"),
    (rf"^Counter to the {O} Remedy$", lambda m: f"{ORD[m[1]]} Remedy'ye counter"),
    (rf"^Counter to the {O} Scholar$", lambda m: f"{ORD[m[1]]} scholar'a counter"),
    (rf"^Counter to the {O} Master$", lambda m: f"{ORD[m[1]]} Master'a counter"),
    (rf"^Counter to the {O} Counter$", lambda m: f"{ORD[m[1]]} counter'a counter"),
    (r"^Counter to the First Three Remedies$", lambda m: "İlk üç remedy'ye counter"),
    (r"^Second Counter to the First and Second Remedies$", lambda m: "Birinci ve İkinci Remedy'ye ikinci counter"),
    (rf"^{O} Remedy Master(.*)$", lambda m: f"{ORD[m[1]]} Remedy Master{m[2]}"),
    (rf"^{O} Scholar(.*)$", lambda m: f"{ORD[m[1]]} scholar{m[2]}"),
    (rf"^{O} Master(.*)$", lambda m: f"{ORD[m[1]]} Master{m[2]}"),
    (rf"^{O} Dueling Sword$", lambda m: f"{ORD[m[1]]} düello kılıcı"),
    (r"^Remedy Master$", lambda m: "Remedy Master"),
    (r"^Three Players$", lambda m: "Üç player"),
    (r"^Two Players$", lambda m: "İki player"),
    (r"^Player$", lambda m: "Player (Zugadore)"),
    (r"^Special Play$", lambda m: "Özel oyun"),
    (r"^Conclusion$", lambda m: "Kitabın sonu"),
    (r"^Upper Sword-Taking(.*)$", lambda m: f"Yukarı disarm (tor di spada){m[1]}"),
    (r"^Middle Sword-Taking$", lambda m: "Orta disarm (tor di spada)"),
    (r"^Lower Sword-Taking$", lambda m: "Aşağı disarm (tor di spada)"),
    (r"^Second Lower Sword-Taking$", lambda m: "İkinci aşağı disarm"),
    (r"^Master of Disarms$", lambda m: "Disarm Master'ı"),
    (r"^Master of Breaks$", lambda m: "Kırma Master'ı"),
    (r"^Master of Locks$", lambda m: "Lock Master'ı"),
    (r"^Master of Throws$", lambda m: "Atış Master'ı"),
    (r"^Master of Strikes$", lambda m: "Vuruş Master'ı"),
]
SUFFIX = [(", the Upper Key", ", chiave di sopra"), (", the Lower Key", ", chiave di sotto"), (", the Gambarola", ", Gambarola"),
          (", the Outsider", ", dıştaki"), (", the Villain’s Strike", ", Colpo di villano"), (" (cont.)", " (devam)"),
          (", the Exchange of", ", Scambiar di punta"), (", the Breaking of", ", Rompere di punta"), (", the Breaking ", ", Rompere di punta"),
          (", the Deceptive", ", Punta falsa"), (", the Decepti", ", Punta falsa")]


def tr_title(t):
    for rx, f in TITLE_RULES:
        m = re.match(rx, t)
        if m:
            out = f(m)
            for a, b in SUFFIX:
                out = out.replace(a, b)
            return out
    return t


def load_tr():
    texts = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "src", "atlas", "fiore_tr", "*.txt"))):
        for line in open(p, encoding="utf-8"):
            line = line.rstrip("\n")
            if line.strip():
                n, t = line.split("|", 1)
                texts[int(n)] = t
    return texts


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


def entry(p, lang, h3, where, body, cat_name):
    ref = f"Getty {p['ref']} · " if p["ref"] else ""
    return (f'<article class="entry">{card(p, lang, h3 + " — " + where, cat_name)}'
            f'<div class="txt"><h3>{esc(h3)}</h3><p class="where">{esc(where)}</p>{body}'
            f'<span class="src">{esc(ref)}{PAGE[lang]} {p["page"]}</span></div></article>')


def para(t):
    t = esc(t)
    return "<p>" + re.sub(r"(\[[^\]]+\])", r'<i class="ed">\1</i>', t) + "</p>"


def lore(items):
    out = []
    for it in items:
        if isinstance(it, tuple):
            out.append(f"<p><b>{esc(it[0])}</b> {esc(it[1])}</p>")
        else:
            out.append(f'<p class="verse">{esc(it)}</p>')
    return '<div class="lore">' + "".join(out) + "</div>"


def build(lang, plays, tr_texts):
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
            if lang == "tr":
                arts = []
                for n in nums:
                    p = plays[n]
                    h3 = entries[n][0][0] if n in entries else tr_title(p["title"])
                    arts.append(entry(p, lang, h3, p["title"], para(tr_texts[n]), title))
                parts.append('<div class="entries" data-gal>' + "".join(arts) + "</div>")
                nums_left = []
            elif entries:
                arts = []
                for n in nums:
                    if n not in entries:
                        continue
                    h3, txt = entries[n][idx]
                    arts.append(f'<article class="entry">{card(plays[n], lang, h3 + " — " + plays[n]["title"], title)}'
                                f'<div class="txt"><h3>{esc(h3)}</h3><p class="where">{esc(plays[n]["title"])}</p>'
                                f'<p>{esc(txt)}</p><span class="src">Getty {esc(plays[n]["ref"])} · {PAGE[lang]} {plays[n]["page"]}</span></div></article>')
                parts.append('<div class="entries" data-gal>' + "".join(arts) + "</div>")
            rest = [] if lang == "tr" else [n for n in nums if n not in entries]
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
            f'  <p class="src-note">{SOURCE_HTML[lang].format(w=WIKTENAUER)}</p>\n</div>\n'
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
    tr_texts = load_tr()
    assert sorted(tr_texts) == sorted(plays), sorted(set(plays) ^ set(tr_texts))
    for lang in ("tr", "en"):
        out = os.path.join(ROOT, "src", "atlas", f"fiore.{lang}.html")
        open(out, "w", encoding="utf-8", newline="\n").write(build(lang, plays, tr_texts))
        print("wrote", out)


if __name__ == "__main__":
    main()
