"""Static site generator for lycian fighters / Antalya HEMA.

Usage: python tools/build.py
Reads src/, writes plain HTML into site/ (images in site/img are produced by
extract.py and brand.py and are left untouched).
"""
import datetime, html, json, os, re, shutil, sys
from bs4 import BeautifulSoup, NavigableString

sys.path.insert(0, os.path.dirname(__file__))
from i18n import translate, TRANSLATABLE_ATTRS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- config
SITE_URL = "https://antalyahema.com"
TODAY = datetime.date.today().isoformat()
PHONE_INTL = "+905345225173"
INSTAGRAM = "https://www.instagram.com/lycian.fighters/"
MAPS = "https://share.google/V4jXBhmK1i5wzDwwB"
WA_TEXT = {
    "tr": "Merhaba, Lycian Fighters hakkında bilgi almak istiyorum.",
    "en": "Hi, I'd like to learn more about Lycian Fighters.",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "site")

PAGES = [
    # key, lang, path (relative URL, "" = site root)
    ("home", "tr", ""),
    ("meyer", "tr", "meyer-1570/"),
    ("liechtenauer", "tr", "liechtenauer/"),
    ("home", "en", "en/"),
    ("meyer", "en", "en/meyer-1570/"),
    ("liechtenauer", "en", "en/liechtenauer/"),
]

META = {
    ("home", "tr"): dict(
        title="Antalya HEMA Kulübü – Lycian Fighters | Uzun Kılıç Eğitimi",
        desc="Antalya'nın ilk HEMA kulübü Lycian Fighters: Tarihi Avrupa Dövüş Sanatları ve uzun kılıç. Kulüp tanıtımı, HEMA rehberi, Meyer ve Liechtenauer atlasları.",
        crumb="Ana sayfa"),
    ("home", "en"): dict(
        title="HEMA Antalya – Lycian Fighters | Longsword Club in Antalya",
        desc="Lycian Fighters, the first HEMA club in Antalya, Türkiye: Historical European Martial Arts and the longsword, with Meyer and Liechtenauer drawing atlases.",
        crumb="Home"),
    ("meyer", "tr"): dict(
        title="Joachim Meyer 1570 Uzun Kılıç Atlası | HEMA Antalya",
        desc="Joachim Meyer'in 1570 tarihli kitabından uzun kılıç duruşları, kesişler, el işi ve güreş: 64 gravür görseli ve Türkçe açıklamalar. Lycian Fighters, HEMA Antalya.",
        h1="Joachim Meyer 1570: Uzun Kılıç Atlası", crumb="Meyer 1570",
        h1_html='<span lang="en">Joachim Meyer</span> <span class="num">1570</span>: Uzun Kılıç Atlası'),
    ("meyer", "en"): dict(
        title="Joachim Meyer 1570 Longsword Atlas | HEMA Antalya",
        desc="Longsword guards, cuts, handwork and wrestling from Joachim Meyer's 1570 treatise: 64 engraved images with explanations. By Lycian Fighters, HEMA Antalya.",
        h1="Joachim Meyer 1570: Longsword Atlas", crumb="Meyer 1570",
        h1_html='Joachim Meyer <span class="num">1570</span>: Longsword Atlas'),
    ("liechtenauer", "tr"): dict(
        title="Liechtenauer Uzun Kılıç ve Zırhlı Dövüş Atlası | HEMA Antalya",
        desc="Liechtenauer geleneğinin dört duruşu, beş usta kesişi, taktikleri, kılıçlı güreş ve zırhlı dövüşü: 138 el yazması çizimi ve Türkçe açıklamalar.",
        h1="Liechtenauer: Uzun Kılıç ve Zırhlı Dövüş Atlası", crumb="Liechtenauer",
        h1_html='<span lang="de">Liechtenauer</span>: Uzun Kılıç ve Zırhlı Dövüş Atlası'),
    ("liechtenauer", "en"): dict(
        title="Liechtenauer Longsword & Armoured Combat Atlas | HEMA Antalya",
        desc="The four guards, five master cuts, tactics, wrestling and armoured combat of the Liechtenauer tradition: 138 manuscript drawings with explanations.",
        h1="Liechtenauer: Longsword & Armoured Combat Atlas", crumb="Liechtenauer"),
}

UI = {
    "tr": dict(
        skip="İçeriğe geç", tagline="Antalya HEMA", menu="Menü",
        nav=[("Kulüp", "#kulup"), ("HEMA nedir?", "#hema-nedir"), ("Antrenman", "#antrenman"),
             ("Meyer 1570", "meyer-1570/"), ("Liechtenauer", "liechtenauer/"),
             ("Basın", "#basin"), ("İletişim", "#iletisim")],
        enc="Ansiklopedi", enc_anchor="#ansiklopedi",
        lb=("Çizim büyütme", "Kapat", "Önceki", "Sonraki"),
        foot_about="Antalya'nın ilk Tarihi Avrupa Dövüş Sanatları (HEMA) kulübü. Uzun kılıç ve tarihi dövüş kaynakları.",
        foot_pages="Sayfalar", foot_contact="İletişim", foot_where="Antrenman yeri",
        cta_h="Bu teknikleri Antalya'da çalışıyoruz",
        cta_p="Lycian Fighters, Antalya'nın ilk HEMA kulübü. Çalışmalarımızı Instagram'da takip edin.",
        cta_btn="Instagram", other="Diğer atlas",
        lang_name="Türkçe", locale="tr_TR"),
    "en": dict(
        skip="Skip to content", tagline="HEMA Antalya", menu="Menu",
        nav=[("Club", "#club"), ("What is HEMA?", "#what-is-hema"), ("Training", "#training"),
             ("Meyer 1570", "meyer-1570/"), ("Liechtenauer", "liechtenauer/"),
             ("Press", "#press"), ("Contact", "#contact")],
        enc="Encyclopedia", enc_anchor="#encyclopedia",
        lb=("Enlarged drawing", "Close", "Previous", "Next"),
        foot_about="The first Historical European Martial Arts (HEMA) club in Antalya, Türkiye. Longsword and historical fencing sources.",
        foot_pages="Pages", foot_contact="Contact", foot_where="Training venue",
        cta_h="We study these techniques in Antalya",
        cta_p="Lycian Fighters is the first HEMA club in Antalya. Follow our work on Instagram.",
        cta_btn="Instagram", other="The other atlas",
        lang_name="English", locale="en_US"),
}

ICONS = {
    "whatsapp": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.47 14.38c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.16-.17.2-.35.22-.64.07-.3-.15-1.26-.46-2.39-1.47-.88-.79-1.48-1.76-1.65-2.06-.17-.3-.02-.46.13-.61.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.61-.92-2.21-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48s1.07 2.88 1.21 3.07c.15.2 2.1 3.2 5.08 4.49.71.31 1.26.49 1.7.63.71.22 1.36.19 1.87.12.57-.09 1.76-.72 2-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35m-5.42 7.4a9.87 9.87 0 0 1-5.03-1.38l-.36-.21-3.74.98 1-3.65-.24-.37a9.86 9.86 0 0 1-1.51-5.26c0-5.45 4.44-9.88 9.89-9.88 2.64 0 5.12 1.03 6.99 2.9a9.83 9.83 0 0 1 2.89 6.99c0 5.45-4.44 9.88-9.89 9.88m8.41-18.3A11.82 11.82 0 0 0 12.05 0C5.5 0 .16 5.34.16 11.89c0 2.1.55 4.14 1.59 5.95L.06 24l6.3-1.65a11.88 11.88 0 0 0 5.68 1.45h.01c6.55 0 11.89-5.34 11.89-11.9a11.82 11.82 0 0 0-3.48-8.41z"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
}

FONTS = ("https://fonts.googleapis.com/css2?family=Alegreya+Sans:ital,wght@0,400;0,500;0,700;1,400"
         "&family=Cinzel:wght@500;700&family=IBM+Plex+Mono:wght@400;500{extra}&display=swap")

ADDRESS = {
    "@type": "PostalAddress",
    "streetAddress": "Molla Yusuf Mah., Hürriyet Cd. No:51, Uncalı",
    "addressLocality": "Konyaaltı",
    "addressRegion": "Antalya",
    "addressCountry": "TR",
}


# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(s, quote=True)


def url_of(path):
    return f"{SITE_URL}/{path}"


def counterpart(key, lang):
    other = "en" if lang == "tr" else "tr"
    return next(p for k, l, p in PAGES if k == key and l == other)


def page_path(key, lang):
    return next(p for k, l, p in PAGES if k == key and l == lang)


def wa_link(lang):
    from urllib.parse import quote
    return f"https://wa.me/{PHONE_INTL.lstrip('+')}?text={quote(WA_TEXT[lang])}"


def ld(obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/ld+json">{s}</script>'


def club_node(lang):
    return {
        "@type": "SportsClub",
        "@id": f"{SITE_URL}/#club",
        "name": "Lycian Fighters",
        "alternateName": ["Lycian Fighters HEMA", "Antalya HEMA Kulübü", "HEMA Antalya", "Antalya HEMA"],
        "description": META[("home", lang)]["desc"],
        "url": url_of(page_path("home", lang)),
        "logo": f"{SITE_URL}/img/brand/emblem-512.png",
        "image": [f"{SITE_URL}/img/brand/og-image.jpg", f"{SITE_URL}/img/brand/banner.png"],
        "telephone": "+90 534 522 51 73",
        "address": ADDRESS,
        "areaServed": {"@type": "City", "name": "Antalya"},
        "sport": "Historical European Martial Arts (HEMA)",
        "foundingDate": "2026-04",
        "founder": {"@type": "Person", "name": "İsmail Can Doğan"},
        "sameAs": [INSTAGRAM],
        "knowsAbout": ["HEMA", "Longsword", "Joachim Meyer", "Johannes Liechtenauer", "Historical European Martial Arts"],
    }


# ---------------------------------------------------------------- layout
def head(key, lang, path, root, extra_ld):
    m = META[(key, lang)]
    tr_path, en_path = (path, counterpart(key, lang)) if lang == "tr" else (counterpart(key, lang), path)
    is_atlas = key != "home"
    fonts = FONTS.format(extra="&family=IM+Fell+English+SC" if is_atlas else "")
    ui = UI[lang]
    other_locale = UI["en" if lang == "tr" else "tr"]["locale"]
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(m['title'])}</title>
<meta name="description" content="{esc(m['desc'])}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url_of(path)}">
<link rel="alternate" hreflang="tr" href="{url_of(tr_path)}">
<link rel="alternate" hreflang="en" href="{url_of(en_path)}">
<link rel="alternate" hreflang="x-default" href="{url_of(tr_path)}">
<meta name="theme-color" content="#0C3436">
<meta name="geo.region" content="TR-07">
<meta name="geo.placename" content="Antalya">
<meta property="og:type" content="{'article' if is_atlas else 'website'}">
<meta property="og:site_name" content="Lycian Fighters · HEMA Antalya">
<meta property="og:title" content="{esc(m['title'])}">
<meta property="og:description" content="{esc(m['desc'])}">
<meta property="og:url" content="{url_of(path)}">
<meta property="og:image" content="{SITE_URL}/img/brand/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{ui['locale']}">
<meta property="og:locale:alternate" content="{other_locale}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="{root}img/brand/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="{root}img/brand/apple-touch-icon.png">
<link rel="manifest" href="{root}site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{fonts}">
<link rel="stylesheet" href="{root}assets/style.css">
<script src="{root}assets/app.js" defer></script>
{extra_ld}
</head>"""


def header(key, lang, path, root):
    ui = UI[lang]
    home = root + ("en/" if lang == "en" else "")
    on_home = key == "home"
    links = []
    for label, href in ui["nav"]:
        if href.startswith("#"):
            h = href if on_home else home + href
            cur = ""
        else:
            h = home + href
            cur = ' aria-current="page"' if page_path(key, lang).endswith(href) and not on_home else ""
        links.append(f'<a href="{h}"{cur}>{esc(label)}</a>')
    tr_href = root + (path if lang == "tr" else counterpart(key, lang))
    en_href = root + (path if lang == "en" else counterpart(key, lang))
    lang_sw = (f'<div class="lang" role="group" aria-label="Dil / Language">'
               f'<a href="{tr_href or "./"}" hreflang="tr" lang="tr" aria-current="{str(lang == "tr").lower()}">TR</a>'
               f'<a href="{en_href}" hreflang="en" lang="en" aria-current="{str(lang == "en").lower()}">EN</a></div>')
    return f"""<body>
<a class="skip" href="#main">{ui['skip']}</a>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="{home or './'}"><img src="{root}img/brand/emblem-96.webp" width="40" height="40" alt=""><span><b lang="en">Lycian Fighters</b><small>{ui['tagline']}</small></span></a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav" aria-label="{ui['menu']}">☰</button>
    <nav class="nav" id="nav" aria-label="{ui['menu']}">{''.join(links)}{lang_sw}</nav>
  </div>
</header>"""


def footer(key, lang, root):
    ui = UI[lang]
    home = root + ("en/" if lang == "en" else "")
    pages = "".join(f'<li><a href="{home + h if not h.startswith("#") else (h if key == "home" else home + h)}">{esc(l)}</a></li>'
                    for l, h in ui["nav"])
    addr = ", ".join([ADDRESS["streetAddress"], ADDRESS["addressLocality"] + " / " + ADDRESS["addressRegion"]])
    return f"""<footer class="site-foot">
  <div class="wrap">
    <div>
      <h2><span lang="en">Lycian Fighters</span> · {ui['tagline']}</h2>
      <p>{esc(ui['foot_about'])}</p>
      <address><b>{ui['foot_where']}:</b> 4x4 Sport Center Uncalı, {esc(addr)}</address>
    </div>
    <div><h2>{ui['foot_pages']}</h2><ul>{pages}</ul></div>
    <div><h2>{ui['foot_contact']}</h2><ul>
      <li><a href="tel:{PHONE_INTL}">0534 522 51 73</a></li>
      <li><a href="{wa_link(lang)}" rel="noopener" target="_blank">WhatsApp</a></li>
      <li><a href="{INSTAGRAM}" rel="noopener" target="_blank">Instagram @lycian.fighters</a></li>
      <li><a href="{MAPS}" rel="noopener" target="_blank">Google Maps</a></li>
    </ul></div>
  </div>
  <div class="wrap copy">© {datetime.date.today().year} Lycian Fighters · Antalya HEMA</div>
</footer>
</body>
</html>
"""


def fill(text, lang, root):
    text = text.replace("{{root}}", root).replace("{{wa}}", esc(wa_link(lang))).replace("{{maps}}", MAPS)
    return re.sub(r"\{\{icon:(\w+)\}\}", lambda m: ICONS[m.group(1)], text)


# ---------------------------------------------------------------- pages
def build_home(lang, path, root):
    faq = json.load(open(os.path.join(SRC, "pages", "faq.json"), encoding="utf-8"))[lang]
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq)
    body = open(os.path.join(SRC, "pages", f"home.{lang}.html"), encoding="utf-8").read()
    body = fill(body, lang, root).replace("{{faq}}", faq_html)
    graph = {"@context": "https://schema.org", "@graph": [
        club_node(lang),
        {"@type": "WebSite", "@id": f"{SITE_URL}/#website", "url": f"{SITE_URL}/",
         "name": "Lycian Fighters · HEMA Antalya", "inLanguage": ["tr", "en"], "publisher": {"@id": f"{SITE_URL}/#club"}},
        {"@type": "FAQPage", "inLanguage": lang, "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
    ]}
    return (head("home", lang, path, root, ld(graph)) + "\n" + header("home", lang, path, root)
            + f'\n<main id="main">\n{body}\n</main>\n' + footer("home", lang, root))


def load_table(name):
    table = {}
    p = os.path.join(SRC, "atlas", f"{name}.en.txt")
    seg = {}
    for line in open(os.path.join(SRC, "atlas", f"{name}.segments.txt"), encoding="utf-8"):
        i, s = line.rstrip("\n").split("|", 1)
        seg[i] = s
    for line in open(p, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip():
            continue
        i, t = line.split("|", 1)
        table[seg[i]] = t
    return table


TURKISH_ONLY = re.compile(r"[ğĞıİşŞçÇ]|\b(ve|bir|ile|için|çizim|duruş|kesiş)\b")


def build_atlas(name, lang, path, root):
    m, ui = META[(name, lang)], UI[lang]
    frag = open(os.path.join(SRC, "atlas", f"{name}.tr.html"), encoding="utf-8").read()
    soup = BeautifulSoup(frag, "html.parser")

    if lang == "en":
        table = load_table(name)
        for node in list(soup.find_all(string=True)):
            if isinstance(node, NavigableString) and node.strip():
                node.replace_with(translate(str(node), table))
        for tag in soup.find_all(True):
            for a in TRANSLATABLE_ATTRS:
                if tag.has_attr(a):
                    tag[a] = translate(tag[a], table)
        for fig in soup.select("figure.card"):
            ttl, cap = fig.select_one(".ttl"), fig.select_one(".cap")
            c = cap.get_text() if cap else ""
            fig["data-cap"] = f"{ttl.get_text()}: {c}" if ttl else c
            fig.img["alt"] = c
        leftovers = sorted({s.strip() for s in soup.find_all(string=True) if TURKISH_ONLY.search(s)})
        leftovers += sorted({t[a] for t in soup.find_all(True) for a in ("alt", "data-cap", "data-meta", "aria-label")
                             if t.has_attr(a) and TURKISH_ONLY.search(t[a])})
        for s in leftovers:
            print(f"  [untranslated?] {name}: {s[:90]}")

    h1 = soup.select_one(".mast h1")
    h1.clear()
    h1.append(BeautifulSoup(m.get("h1_html", esc(m["h1"])), "html.parser"))
    for chip in soup.select(".chip"):
        chip["type"] = "button"
        chip["aria-pressed"] = "true" if "on" in chip.get("class", []) else "false"
    for g in soup.select(".group"):
        if not g.get("id"):
            g["id"] = "g" + g["data-group"]
    for im in soup.find_all("img"):
        fn = im["src"]
        im["src"] = f"{root}img/{name}/thumbs/{fn}"
        im["data-full"] = f"{root}img/{name}/{fn}"
        im["decoding"] = "async"

    home = root + ("en/" if lang == "en" else "")
    other = "liechtenauer" if name == "meyer" else "meyer"
    om = META[(other, lang)]
    crumbs = (f'<div class="wrap"><nav class="crumbs" aria-label="breadcrumb"><ol>'
              f'<li><a href="{home or "./"}">{META[("home", lang)]["crumb"]}</a></li>'
              f'<li><a href="{home or "./"}{ui["enc_anchor"]}">{ui["enc"]}</a></li>'
              f'<li aria-current="page">{m["crumb"]}</li></ol></nav></div>')
    after = f"""<div class="wrap">
  <div class="atlas-cta"><div><h2>{esc(ui['cta_h'])}</h2><p>{esc(ui['cta_p'])}</p></div>
  <a class="btn btn-gold" href="{INSTAGRAM}" rel="noopener" target="_blank">{ICONS['instagram']}{esc(ui['cta_btn'])}</a></div>
  <div class="atlas-more"><a class="book" href="{root}{page_path(other, lang)}"><div><div class="eyebrow">{ui['other']}</div><h3>{om.get('h1_html', esc(om['h1']))}</h3><p>{esc(om['desc'])}</p></div></a></div>
</div>"""
    lb = ui["lb"]
    lightbox = f"""<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="{lb[0]}">
  <img id="lbimg" alt="">
  <div class="lbcap" id="lbcap"></div>
  <button class="x" id="lbx" type="button" aria-label="{lb[1]}">×</button>
  <button class="pv" id="lbp" type="button" aria-label="{lb[2]}">‹</button>
  <button class="nx" id="lbn" type="button" aria-label="{lb[3]}">›</button>
</div>"""

    imgs = [f"{SITE_URL}/img/{name}/{im['data-full'].rsplit('/', 1)[-1]}" for im in soup.find_all("img")[:3]]
    graph = {"@context": "https://schema.org", "@graph": [
        {"@type": "SportsClub", "@id": f"{SITE_URL}/#club", "name": "Lycian Fighters", "url": url_of(page_path("home", lang))},
        {"@type": "Article", "headline": m["h1"], "description": m["desc"], "inLanguage": lang,
         "url": url_of(path), "mainEntityOfPage": url_of(path), "image": imgs,
         "author": {"@id": f"{SITE_URL}/#club"}, "publisher": {"@id": f"{SITE_URL}/#club"},
         "datePublished": "2026-10-20", "dateModified": TODAY,
         "about": [{"@type": "Thing", "name": n} for n in (
             ["Joachim Meyer", "Longsword", "Historical European Martial Arts"] if name == "meyer"
             else ["Johannes Liechtenauer", "Longsword", "Kampffechten", "Historical European Martial Arts"])]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": META[("home", lang)]["crumb"], "item": url_of(page_path("home", lang))},
            {"@type": "ListItem", "position": 2, "name": ui["enc"], "item": url_of(page_path("home", lang)) + ui["enc_anchor"]},
            {"@type": "ListItem", "position": 3, "name": m["crumb"], "item": url_of(path)}]},
    ]}
    body = soup.decode(formatter="minimal")
    return (head(name, lang, path, root, ld(graph)) + "\n" + header(name, lang, path, root)
            + f'\n<main id="main" class="atlas atlas-{name}">\n{crumbs}\n{body}\n{after}\n</main>\n{lightbox}\n'
            + footer(name, lang, root))


def write(path, text):
    full = os.path.join(OUT, path.replace("/", os.sep))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def extras():
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for key, lang, path in PAGES:
        alt_tr = path if lang == "tr" else counterpart(key, lang)
        alt_en = path if lang == "en" else counterpart(key, lang)
        sm.append(f"  <url><loc>{url_of(path)}</loc><lastmod>{TODAY}</lastmod>"
                  f'<xhtml:link rel="alternate" hreflang="tr" href="{url_of(alt_tr)}"/>'
                  f'<xhtml:link rel="alternate" hreflang="en" href="{url_of(alt_en)}"/>'
                  f'<xhtml:link rel="alternate" hreflang="x-default" href="{url_of(alt_tr)}"/>'
                  f"<priority>{'1.0' if key == 'home' else '0.8'}</priority></url>")
    sm.append("</urlset>\n")
    write("sitemap.xml", "\n".join(sm))
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    write("site.webmanifest", json.dumps({
        "name": "Lycian Fighters · HEMA Antalya", "short_name": "Lycian Fighters", "lang": "tr",
        "start_url": "./", "display": "browser", "background_color": "#0C3436", "theme_color": "#0C3436",
        "icons": [{"src": "img/brand/emblem-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "img/brand/emblem-512.png", "sizes": "512x512", "type": "image/png"}]},
        ensure_ascii=False, indent=2) + "\n")
    write("404.html", f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sayfa bulunamadı | Lycian Fighters</title><meta name="robots" content="noindex">
<link rel="icon" href="{SITE_URL}/favicon.ico"><link rel="stylesheet" href="{SITE_URL}/assets/style.css"></head>
<body><main class="section"><div class="wrap" style="text-align:center">
<img src="{SITE_URL}/img/brand/emblem-192.png" width="120" height="120" alt="">
<h1 class="title">Sayfa bulunamadı · Page not found</h1>
<p><a href="{SITE_URL}/">Ana sayfa</a> · <a href="{SITE_URL}/en/">Home (English)</a></p></div></main></body></html>
""")
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for f in ("style.css", "app.js"):
        shutil.copyfile(os.path.join(SRC, "assets", f), os.path.join(OUT, "assets", f))


def main():
    for key, lang, path in PAGES:
        root = "../" * path.count("/")
        page = build_home(lang, path, root) if key == "home" else build_atlas(key, lang, path, root)
        write(path + "index.html", page)
        print(f"wrote /{path}index.html ({len(page) // 1024} KB)")
    extras()
    print("site built in", OUT, "for", SITE_URL)


if __name__ == "__main__":
    main()
