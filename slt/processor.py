from typing import Dict, Tuple
import csv

import spacy

from slt import settings
from slt.entities import Sentence, Word, Status
from slt.synonyms import WordnetWithW2vThresholdExtractor, SynonymExtractor
from slt.conjugation import Conjugator


class Processor:
    def __init__(
        self, synonyms_extractor: SynonymExtractor, nlp, jlpt_words: Dict[str, int]
    ):
        self.synonyms_extractor = synonyms_extractor
        self.nlp = nlp
        self.jlpt_words = jlpt_words
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
                verb_text, old_token.lemma_, new_word
            )
        return new_word

    def compute_token(self, token):
        word_level = self.jlpt_words.get(token.lemma_, 1)
        synonyms = self.get_sorted_synonyms(token, max_word_level=word_level)
        if synonyms:
            return synonyms[0]
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
            # print(token.text, token.lemma_, token.dep_, token.pos_, token.tag_)
            new_word_surface = self.compute_token(token)
            if new_word_surface == token.text:
                new_word = Word(new_word_surface, status=Status.UNCHANGED)
                old_sentence.append(Word(token.text, status=Status.UNCHANGED))
                count_to_replace = 1
            else:
                new_word_surface = self.adjust_token(token, new_word_surface)
                new_word = Word(new_word_surface, status=Status.ADDED)
                old_sentence.append(Word(token.text, status=Status.REMOVED))
                count_to_replace = self.get_count_to_replace(token)

            for j in range(i, i + count_to_replace):
                seen.add(j)

            new_sentence.append(new_word)

        return new_sentence, old_sentence

    def get_count_to_replace(self, token):
        if token.pos_ == "VERB":
            return len(self.get_verb_tokens(token))
        return 1

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
            jlpt_words = {row["word"]: int(row["level"]) for row in csv.DictReader(f)}
        return cls(synonyms_extractor, nlp, jlpt_words)


# parser = Parser.load()
# new_tokens, old_tokens = parser.process_sentence("ご希望の日付を選択して下さい")
