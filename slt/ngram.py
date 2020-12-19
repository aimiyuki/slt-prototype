from __future__ import annotations

import argparse
import gzip
import json
import logging
import multiprocessing
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from itertools import islice
from typing import Dict, Iterable, List, OrderedDict, Tuple

import spacy

from slt import settings


def make_defaultdict_int():
    return defaultdict(int)


@dataclass
class NGrams:
    n: int
    grams: Dict[Tuple[str, ...], int] = field(default_factory=make_defaultdict_int)
    total_count: int = 0
    unique_count: int = 0

    def add_entry(self, key: Tuple[str]):
        if key not in self.grams:
            self.unique_count += 1
        self.total_count += 1
        self.grams[key] += 1

    def merge(self, other: NGrams):
        for key, count in other.grams.items():
            if key not in self.grams:
                self.unique_count += 1
            self.grams[key] += count
            self.total_count += other.total_count

    def prune(self, limit: int = None):
        grams = sorted(self.grams.items(), key=lambda x: -x[1])
        if limit is not None:
            grams = grams[:limit]
        self.grams = OrderedDict(grams)

    def to_dict(self):
        result = vars(self)
        result["grams"] = list(self.grams.items())
        return result


class NGramsContainer:
    def __init__(self, max_n: int = 2):
        self.max_n = max_n
        self.ngrams = {i: NGrams(i) for i in range(1, max_n + 1)}

    def add_entries(self, tokens: List[str]):
        for i in range(1, self.max_n + 1):
            key = tuple(str(v) for v in tokens[:i])
            if len(key) == i:
                self.ngrams[i].add_entry(key)

    def merge(self, other: NGramsContainer):
        for n, grams in other.ngrams.items():
            self.ngrams[n].merge(grams)

    def prune(self, limits: Dict[int, int]):
        for n, grams in self.ngrams.items():
            grams.prune(limits.get(n))

    def to_dict(self):
        return {n: grams.to_dict() for n, grams in self.ngrams.items()}


class NGramGenerator:
    def __init__(self):
        self.nlp = None

    def load_model(self):
        self.nlp = spacy.load("ja_core_news_sm", disable=["ner"])

    def generate_document_ngrams(self, document: str) -> NGramsContainer:
        ngrams = NGramsContainer()
        doc = self.nlp(document)
        for i in range(len(doc)):
            ngrams.add_entries(doc[i:])
        return ngrams


def generate_corpus_ngrams(corpus: Iterable[str]) -> NGramsContainer:
    ngram_gen = NGramGenerator()
    ngram_gen.load_model()
    cores = multiprocessing.cpu_count()
    ngrams = NGramsContainer()
    with ProcessPoolExecutor(
        max_workers=cores - 2, initializer=ngram_gen.load_model
    ) as executor:
        for i, corpus_ngrams in enumerate(
            executor.map(ngram_gen.generate_document_ngrams, corpus, chunksize=128)
        ):
            if i % 100 == 0:
                logging.info("done: %s", i)
            ngrams.merge(corpus_ngrams)
    return ngrams


def read_articles_content(filepath: str, docs_limit: int = None) -> Iterable[str]:
    with gzip.open(filepath, "r") as f:
        for line in islice(f, None, docs_limit):
            parsed = json.loads(line)
            yield parsed["content"]


def main():
    logging.basicConfig(level=logging.INFO, format=settings.LOG_FORMAT)
    parser = argparse.ArgumentParser(prog="ngram")
    parser.add_argument("file", help="file containing corpus")
    parser.add_argument("-o", "--output", required=True, help="output file")
    parser.add_argument(
        "-u",
        "--unigram-count",
        type=int,
        help="numbers of unigrams to keep",
        default=300_000,
    )
    parser.add_argument(
        "-b",
        "--bigram-count",
        type=int,
        help="numbers of bigrams to keep",
        default=1_000_000,
    )
    parser.add_argument(
        "-l", "--limit", type=int, help="Limit number of documents to process"
    )
    args = parser.parse_args()

    corpus = read_articles_content(args.file, args.limit)
    ngrams = generate_corpus_ngrams(corpus)
    limits = {1: args.unigram_count, 2: args.bigram_count}
    ngrams.prune(limits)
    with gzip.open(args.output, "wt") as f:
        json.dump(ngrams.to_dict(), f)


if __name__ == "__main__":
    main()
