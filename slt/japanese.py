import re


ALPHABET_RE = re.compile("[a-zA-Z]+")
KANJI_RE = re.compile(
    "[\u2E80-\u2FDF\u3005-\u3007\u3400-\u4DBF\u4E00-\u9FFF"
    "\uF900-\uFAFF\U00020000-\U0002EBEF]+"
)
HIRAGANA_RE = re.compile("[ぁ-ゟ]+")
ONLY_HIRAGANA_RE = re.compile("^[ぁ-ゟ]+$")
KATAKANA_RE = re.compile("[\u30A1-\u30FF]+")


def has_kanji(token: str) -> bool:
    return KANJI_RE.search(token) is not None


def has_hiragana(token: str) -> bool:
    return HIRAGANA_RE.search(token) is not None


def only_hiragana(token: str) -> bool:
    return ONLY_HIRAGANA_RE.match(token) is not None


def has_katakana(token: str) -> bool:
    return KATAKANA_RE.search(token) is not None


def has_alphabet(token: str) -> bool:
    return ALPHABET_RE.search(token) is not None
