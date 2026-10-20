"""Shared helpers for splitting atlas text into translatable parts.

A text node or attribute is split on " · " separators; each part is either
handled by a rule (page/plate numbers), looked up in the translation table,
or left as-is (German terms, captions that are already English).
"""
import re

SEP = " · "
TRANSLATABLE_ATTRS = ("data-meta", "aria-label", "title")

RULES = [
    (re.compile(r"^s\. ?(\d+)$"), r"p. \1"),
    (re.compile(r"^metin (s\..+)$"), lambda m: "text " + m.group(1).replace("s.", "p.")),
    (re.compile(r"^kitapta (s\..+)$"), lambda m: "book " + m.group(1).replace("s.", "p.")),
    (re.compile(r"^Plaka ([A-Z])$"), r"Plate \1"),
]
INLINE = [
    (" (devam)", " (cont.)"),
]


def has_letters(s):
    return bool(re.search(r"[A-Za-zÀ-ÿĞğİıŞşÇçÖöÜü]", s))


def apply_rules(part):
    for rx, rep in RULES:
        if rx.match(part):
            return rx.sub(rep, part)
    return None


def parts_of(text):
    """Yield the stripped parts that may need a dictionary translation."""
    for p in text.split(SEP):
        p = p.strip()
        if p and has_letters(p) and apply_rules(p) is None:
            yield p


def translate(text, table):
    lead = text[: len(text) - len(text.lstrip())]
    trail = text[len(text.rstrip()):]
    out = []
    for p in text.strip().split(SEP):
        q = p.strip()
        r = apply_rules(q)
        if r is None:
            r = table.get(q, q)
        for a, b in INLINE:
            r = r.replace(a, b)
        out.append(r)
    return lead + SEP.join(out) + trail
