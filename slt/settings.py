import os
from os import path
from dotenv import load_dotenv


PROJECT_ROOT = path.dirname(path.dirname(__file__))

load_dotenv()


WORDNET_DB_PATH = path.expanduser(
    os.environ.get("WORDNET_DB_PATH", "~/.local/share/models/wnjpn.db")
)
W2V_MODEL_PATH = path.expanduser(
    os.environ.get("W2V_MODEL_PATH", "~/.local/share/models/cc.ja.300.bin")
)
JAPANESE_MODEL = os.environ.get("JAPANESE_MODEL", "ja_core_news_sm")
JLPT_WORDS_PATH = os.environ.get("JLPT_WORDS_PATH", "../data/jlpt-vocab.csv")

NGRAMS_PATH = path.expanduser(
    os.environ.get("NGRAMS_PATH", "~/.local/share/models/wiki-ja-ngrams.json.gz")
)

CONJUGATOR_DATA = path.join(PROJECT_ROOT, "data/conjo.csv")
VERBS_PATH = path.join(PROJECT_ROOT, "data/verbs.csv")

LOG_FORMAT = "%(asctime)-15s - %(levelname)s - %(message)s"
