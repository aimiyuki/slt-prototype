from typing import List
from abc import ABC, abstractmethod
from functools import lru_cache
import threading
import sqlite3

import numpy as np
from gensim.models.keyedvectors import KeyedVectors


CACHE_SIZE = 10_000
DEFAULT_SIMILARITY_THRESHOLD = 0.4


thread_local = threading.local()


def load_word2vec_model(model_path: str, is_binary: bool = None):
    if is_binary is None:
        is_binary = model_path.endswith(".bin")
    return KeyedVectors.load_word2vec_format(model_path, binary=is_binary)


class SynonymExtractor(ABC):  # pylint: disable=too-few-public-methods
    """Base class for synonyms extractor"""

    @abstractmethod
    def find_synonyms(self, word: str, topn: int = 10, pos: str = "") -> List[str]:
        """Extract ``topn`` synonyms of ``word``"""


class WithWordnet:  # pylint: disable=too-few-public-methods
    pos_mapping = {"NOUN": "n", "VERB": "v", "ADJ": "a"}

    def __init__(self, db_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = db_path

    @property
    def db(self):
        if not hasattr(thread_local, "wordnet_db"):
            thread_local.wordnet_db = sqlite3.connect(self.db_path)
        return thread_local.wordnet_db

    def pos_to_wordnet(self, pos: str) -> str:
        return self.pos_mapping.get(pos, "r")


class Word2vecSynonymExtractor(SynonymExtractor):
    def __init__(self, model):
        """Uses word2vec to find synonyms"""
        self.model = model

    @lru_cache(maxsize=CACHE_SIZE)
    def find_synonyms(self, word: str, topn: int = 10, pos: str = "") -> List[str]:
        if word not in self.model:
            return []
        return [v[0] for v in self.model.most_similar(word, topn=topn)]

    @classmethod
    def load(cls, model_path, is_binary=None):
        model = load_word2vec_model(model_path, is_binary=is_binary)
        return cls(model)


class WordnetSynonymExtractor(WithWordnet, SynonymExtractor):
    SYNONYM_QUERY = """
        SELECT DISTINCT lemma FROM word w
        JOIN sense s ON w.wordid = s.wordid
        WHERE w.lang = ? AND w.lemma <> ? AND s.synset IN (
                SELECT s2.synset
                FROM word w
                JOIN sense s ON w.wordid = s.wordid
                JOIN synset s2 ON s.synset = s2.synset
                WHERE w.lemma = ?
                {pos_condition}
        )
        {limit}
    """

    def __init__(self, db_path: str, lang: str):
        """Uses wordnet to find synonyms"""
        super().__init__(db_path)
        self.lang = lang

    @lru_cache(maxsize=CACHE_SIZE)
    def find_synonyms(self, word: str, topn: int = 10, pos: str = "") -> List[str]:
        cursor = self.db.cursor()
        args = (self.lang, word, word)
        format_args = dict(pos_condition="", limit="")
        if pos:
            format_args["pos_condition"] = " AND s2.pos = ?"
            args += (self.pos_to_wordnet(pos),)
        if topn > 0:
            format_args["limit"] = " LIMIT ?"
            args += (topn,)
        query = self.SYNONYM_QUERY.format(**format_args)
        cursor.execute(query, args)
        return [v[0] for v in cursor.fetchall()]

    @classmethod
    def load(cls, db_path: str, lang: str = "jpn"):
        return cls(db_path, lang)


class IntersectionSynonymExtractor(
    SynonymExtractor
):  # pylint: disable=too-few-public-methods
    # fetch 10 times more than topn
    FETCH_FACTOR: int = 10

    def __init__(
        self, extractors: List[SynonymExtractor], fallback: SynonymExtractor = None
    ):
        """Combines multiple synonym extractors and returns the result
        If the extractors do not have any words in common, ``fallback`` will
        be used instead if provided
        """
        self.extractors = extractors
        self.fallback = fallback

    @lru_cache(maxsize=CACHE_SIZE)
    def find_synonyms(self, word: str, topn: int = 10, pos: str = "") -> List[str]:
        max_results = self.FETCH_FACTOR * topn
        synonyms = [
            extractor.find_synonyms(word, topn=max_results, pos=pos)
            for extractor in self.extractors
        ]
        candidates = set(w for s in synonyms[1:] for w in s)
        results = []
        # keep ordering of the first extractor synonyms
        for candidate in synonyms[0]:
            if candidate in candidates:
                results.append(candidate)
                if len(results) >= topn:
                    break
        if self.fallback and not results:
            return self.fallback.find_synonyms(word, topn=topn, pos=pos)
        return results


class WordnetWithW2vThresholdExtractor(WordnetSynonymExtractor):
    def __init__(
        self,
        db_path: str,
        model: KeyedVectors,
        lang: str,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ):
        """Uses wordnet to find synonyms"""
        super().__init__(db_path, lang)
        self.model = model
        self.similarity_threshold = similarity_threshold

    @lru_cache(maxsize=CACHE_SIZE)
    def find_synonyms(self, word: str, topn: int = 10, pos: str = "") -> List[str]:
        candidates = super().find_synonyms(word, topn=-1, pos=pos)
        scores = [self.similarity(word, c) for c in candidates]
        sorted_indices = np.argsort(scores)[::-1]
        return [
            candidates[i]
            for i in sorted_indices[:topn]
            if scores[i] >= self.similarity_threshold
        ]

    def similarity(self, word1: str, word2: str) -> float:
        if word1 in self.model and word2 in self.model:
            return self.model.similarity(word1, word2)
        # if not in vocabulary, accept but make it the
        # lowest possible score
        return self.similarity_threshold

    @classmethod
    def load(
        cls, model_path: str, db_path: str, lang: str = "jpn", is_binary: bool = None
    ):  # pylint: disable=arguments-differ
        model = load_word2vec_model(model_path, is_binary=is_binary)
        return cls(db_path, model, lang)
