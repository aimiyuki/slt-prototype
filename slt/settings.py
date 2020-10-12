import os
from os import path


PROJECT_ROOT = path.dirname(path.dirname(__file__))


WORDNET_DB_PATH = os.environ.get(
    "WORDNET_DB_PATH", path.expanduser("~/.local/share/models/wnjpn.db")
)
W2V_MODEL_PATH = os.environ.get(
    "W2V_MODEL_PATH", path.expanduser("~/.local/share/models/cc.ja.300.bin")
)
JAPANESE_MODEL = os.environ.get("JAPANESE_MODEL", "ja_core_news_sm")
JLPT_WORDS_PATH = os.environ.get("JLPT_WORDS_PATH", "../data/jlpt-vocab.csv")

CONJUGATOR_DATA = path.join(PROJECT_ROOT, "data/conjo.csv")
VERBS_PATH = path.join(PROJECT_ROOT, "data/verbs.csv")
