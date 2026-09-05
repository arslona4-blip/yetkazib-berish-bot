"""Kirill ↔ lotin: qidiruvda «гуруч» ≈ «guruch»."""

from __future__ import annotations

import re

# Uzbek/rus kirill → lotin (digraflar avval)
_CYR_DIGRAPHS: tuple[tuple[str, str], ...] = (
    ("щ", "sh"),
    ("ш", "sh"),
    ("ч", "ch"),
    ("ц", "ts"),
    ("ё", "yo"),
    ("ю", "yu"),
    ("я", "ya"),
    ("ў", "o'"),
    ("ғ", "g'"),
)

_CYR_LETTERS = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ж": "j",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "x",
        "ъ": "'",
        "ы": "i",
        "ь": "",
        "э": "e",
        "қ": "q",
        "ҳ": "h",
        "ң": "ng",
    }
)

# Tez-tez uchraydigan ruscha ovqat so‘zlari → katalog lotin nomi
_SEARCH_ALIASES: dict[str, str] = {
    "ris": "guruch",
    "myaso": "gosht",
    "govyadina": "gosht",
    "baranina": "gosht",
    "kuritsa": "tovuq",
    "moloko": "sut",
    "maslo": "yog",
    "podsolnechnoe": "yog",
    "luk": "piyoz",
    "morkov": "sabzi",
    "morkovka": "sabzi",
    "kartofel": "kartoshka",
    "kartoshka": "kartoshka",
    "sakhar": "shakar",
    "chay": "choy",
    "yaytso": "tuxum",
    "yayca": "tuxum",
    "hleb": "non",
    "muka": "un",
    "goroh": "noxat",
    "tomat": "pomidor",
    "pomidor": "pomidor",
    "perec": "qalampir",
    "plov": "osh",
    "palov": "osh",
}


def cyrillic_to_latin(text: str) -> str:
    """Кирилл матнни lotinga o‘giradi; lotin o‘zgarishsiz qoladi."""
    s = (text or "").lower()
    if not s:
        return ""
    # Faqat kirill bo‘lsa ham, aralash bo‘lsa ham
    for a, b in _CYR_DIGRAPHS:
        s = s.replace(a, b)
    s = s.translate(_CYR_LETTERS)
    return s


def apply_search_aliases(text: str) -> str:
    """Tokenlardan ba’zi ruscha sinonimlarni o‘zbekcha/katalog shakliga."""
    s = (text or "").strip()
    if not s:
        return s

    def _one(tok: str) -> str:
        t = tok.strip("'").strip()
        return _SEARCH_ALIASES.get(t, tok)

    parts = re.split(r"(\W+)", s)
    return "".join(_one(p) if p and not re.match(r"\W+", p) else p for p in parts)


def to_search_text(text: str) -> str:
    """Qidiruv uchun: lower + kirill→lotin + sinonim."""
    s = cyrillic_to_latin(text or "")
    s = (
        s.replace("‘", "'")
        .replace("’", "'")
        .replace("ʻ", "'")
        .replace("`", "'")
    )
    s = apply_search_aliases(s)
    return s
