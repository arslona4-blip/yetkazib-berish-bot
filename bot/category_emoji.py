"""Toifa emoji — nomdan taxmin yoki qo‘lda."""

from __future__ import annotations

import re

# Unicode emoji / pictograph at start
_EMOJI_PREFIX = re.compile(
    r"^("
    r"[\U0001F300-\U0001FAFF]"
    r"|[\U00002600-\U000027BF]"
    r"|[\U0001F1E0-\U0001F1FF]"
    r"|[\U00002702-\U000027B0]"
    r")"
    r"\s*"
)

# (kalit so‘zlar, emoji) — birinchi mos kelgani
_EMOJI_RULES: list[tuple[tuple[str, ...], str]] = [
    (("ichimlik", "suv", "cola", "fanta", "sok", "choy", "kofe", "coffee", "energy", "napitok", "napitk"), "🥤"),
    (("non", "bulochka", "pishiriq", "lavash", "samsa", "bread"), "🍞"),
    (("meva", "sabzavot", "olma", "banan", "pomidor", "fruit"), "🍎"),
    (("sut", "yogurt", "yogurt", "pishloq", "qatiq", "sariyog", "milk", "molli"), "🥛"),
    (("go'sht", "gosht", "kolbasa", "tovuq", "mol", "qazi", "meat"), "🥩"),
    (("baliq", "dengiz", "fish"), "🐟"),
    (("shirinlik", "konfet", "muzqaymoq", "shokolad", "tort", "pechenye", "candy", "ice"), "🍬"),
    (("chip", "snack", "pepsi", "lays", "cracker"), "🍿"),
    (("parfyum", "kosmetik", "krem", "labial", "makeup", "atır"), "💄"),
    (("kantselyar", "ruchka", "daftar", "qalam", "stationery"), "✏️"),
    (("uy", "tozalik", "sovun", "kir", "yumshatgich", "household"), "🏠"),
    (("bolalar", "o'yinchoq", "oyinchoq", "kids", "baby"), "🧸"),
    (("sigaret", "tamaki", "tobacco"), "🚬"),
    (("dor", "apteka", "vitamin", "medicine"), "💊"),
    (("oshxona", "idish", "qoshiq", "kitchen"), "🍽️"),
    (("oziq", "ovqat", "taom", "food", "grocery"), "🛒"),
    (("muzlatilgan", "muzlatilgan", "frozen"), "🧊"),
    (("gazli", "mineral"), "💧"),
]


def extract_leading_emoji(text: str) -> tuple[str, str]:
    """(emoji yoki '', qolgan matn)."""
    raw = (text or "").strip()
    if not raw:
        return "", ""
    m = _EMOJI_PREFIX.match(raw)
    if not m:
        return "", raw
    return m.group(1), raw[m.end() :].strip()


def guess_category_emoji(name: str) -> str:
    """Nomdagi kalit so‘zdan emoji tanlaydi."""
    lead, rest = extract_leading_emoji(name)
    if lead:
        return lead
    key = (rest or name or "").casefold()
    for words, emoji in _EMOJI_RULES:
        if any(w in key for w in words):
            return emoji
    return "📦"


def parse_category_name(raw: str) -> tuple[str, str]:
    """Yangi toifa matnidan (emoji, toza nom)."""
    text = (raw or "").strip()
    emoji, rest = extract_leading_emoji(text)
    name = rest or text
    if not emoji:
        emoji = guess_category_emoji(name)
    return emoji, name


def category_label(category) -> str:
    """Ro‘yxatda ko‘rsatish: 🥤 Ichimliklar."""
    try:
        name = str(category["name"] or "").strip()
    except (KeyError, TypeError, IndexError):
        name = str(category or "").strip()
    try:
        emoji = str(category["emoji"] or "").strip()
    except (KeyError, TypeError, IndexError):
        emoji = ""
    if not emoji:
        emoji = guess_category_emoji(name)
    # Nom boshida shu emoji bo‘lsa — takrorlamaslik
    lead, rest = extract_leading_emoji(name)
    display = rest if lead == emoji and rest else name
    return f"{emoji} {display}".strip()
