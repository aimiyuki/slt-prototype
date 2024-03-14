import gzip
import re
import json
from slt.ngram import NGramsContainer
from typing import Dict, Tuple
import csv

import spacy

from slt import japanese, settings
from slt.entities import Sentence, Word, Status
from slt.synonyms import WordnetWithW2vThresholdExtractor, SynonymExtractor
from slt.conjugation import Conjugator


NGRAM_RATIO_THRESHOLD = 10


class Processor:
    def __init__(
        self,
        synonyms_extractor: SynonymExtractor,
        nlp,
        jlpt_words: Dict[str, int],
        ngrams: NGramsContainer,
    ):
        self.synonyms_extractor = synonyms_extractor
        self.nlp = nlp
        self.jlpt_words = jlpt_words
        self.ngrams = ngrams
        self.conjugator = Conjugator()

    def get_sorted_synonyms(self, token, max_word_level=0):
        result = []
        for candidate in self.synonyms_extractor.find_synonyms(
            token.lemma_, topn=-1, pos=token.pos_
        ):
            candidate_level = self.jlpt_words.get(candidate, 1)
            if candidate_level <= max_word_level:
                continue
            result.append(candidate)
        return result

    def adjust_token(self, old_token: spacy.tokens.token.Token, new_word: str):
        if old_token.pos_ == "VERB":
            verb_tokens = self.get_verb_tokens(old_token)
            verb_text = "".join([t.text for t in verb_tokens])
            return self.conjugator.adjust_conjugation(
                verb_text, [t.lemma_ for t in verb_tokens], new_word
            )
        return new_word

    def compute_token(self, token):
        if token.pos_ == "AUX" or japanese.only_hiragana(token.text):
            return token.text
        word_level = self.jlpt_words.get(token.lemma_, 1)
        synonyms = self.get_sorted_synonyms(token, max_word_level=word_level)

        for candidate in synonyms:
            before, after = self.get_count_to_replace(token, candidate)
            if token.idx > before and token.pos_ in ["NOUN", "ADJ"]:
                previous_token = token.nbor(-1 - before)
                current_ngram = self.ngrams[previous_token.text + token.text]
                new_ngram = self.ngrams[previous_token.text + candidate]
                if (
                    (new_ngram == 0 and current_ngram > 0)
                    or new_ngram > 0
                    and current_ngram / new_ngram > NGRAM_RATIO_THRESHOLD
                ):
                    continue
            if token.idx + after < len(token.doc) and token.pos_ in ["NOUN", "ADJ"]:
                next_token = token.nbor(1 + after)
                current_ngram = self.ngrams[token.text + next_token.text]
                new_ngram = self.ngrams[candidate + next_token.text]
                if (new_ngram == 0 and current_ngram > 0) or (
                    new_ngram > 0 and current_ngram / new_ngram > NGRAM_RATIO_THRESHOLD
                ):
                    continue
            return candidate

        return token.text

    def process_sentence(self, sentence) -> Tuple[Sentence, Sentence]:
        doc = self.nlp(sentence)
        old_sentence = Sentence()
        new_sentence = Sentence()
        seen = set()
        for i, token in enumerate(doc):
            if i in seen:
                old_sentence.append(Word(token.text, status=Status.REMOVED))
                continue
            new_word_surface = self.compute_token(token)
            if new_word_surface != token.text:
                new_word_surface = self.adjust_token(token, new_word_surface)
            if new_word_surface == token.text:
                new_word = Word(new_word_surface, status=Status.UNCHANGED)
                old_sentence.append(Word(token.text, status=Status.UNCHANGED))
                before, after = 0, 0
            else:
                new_word = Word(new_word_surface, status=Status.ADDED)
                old_sentence.append(Word(token.text, status=Status.REMOVED))
                before, after = self.get_count_to_replace(token, new_word_surface)

            for j in range(i, i + after + 1):
                seen.add(j)

            if before > 0:
                new_sentence = new_sentence[:-before]

            new_sentence.append(new_word)

        return new_sentence, old_sentence

    def get_count_to_replace(self, token, new_word_surface) -> Tuple[int, int]:
        before, after = 0, 0
        if token.pos_ == "VERB":
            after = len(self.get_verb_tokens(token)) - 1
        elif (
            token.pos_ == "ADJ"
            and [t.text for t in token.rights][:1] in [["な"], ["だ"]]
            and new_word_surface.endswith("い")
            or new_word_surface.endswith("かった")
        ):
            after = 1

        lefts = list(token.lefts)
        if lefts and lefts[-1].pos_ == "INTJ" and lefts[-1].text in ["お", "ご"]:
            before = 1

        return (before, after)

    @staticmethod
    def get_verb_tokens(root):
        tokens = [root]
        for token in root.rights:
            if token.dep_ in ["aux", "mark"]:
                tokens.append(token)
            else:
                break
        return tokens

    @classmethod
    def load(
        cls,
        wordnet_db_path=settings.WORDNET_DB_PATH,
        w2v_model_path=settings.W2V_MODEL_PATH,
        japanese_model=settings.JAPANESE_MODEL,
        jlpt_words_path=settings.JLPT_WORDS_PATH,
        ngrams_path=settings.NGRAMS_PATH,
        w2v=None,
    ):
        if w2v:
            synonyms_extractor = WordnetWithW2vThresholdExtractor(
                wordnet_db_path, w2v, lang="jpn"
            )
        else:
            synonyms_extractor = WordnetWithW2vThresholdExtractor.load(
                w2v_model_path, wordnet_db_path
            )
        nlp = spacy.load(japanese_model)
        with open(jlpt_words_path) as f:
            jlpt_words = {
                w: int(row["level"])
                for row in csv.DictReader(f)
                for w in re.split(r"\s+|、", row["word"])
            }
        with gzip.open(ngrams_path) as f:
            ngrams = NGramsContainer.from_dict(json.load(f))
        return cls(synonyms_extractor, nlp, jlpt_words, ngrams=ngrams)


# parser = Parser.load()
# new_tokens, old_tokens = parser.process_sentence("ご希望の日付を選択して下さい")
