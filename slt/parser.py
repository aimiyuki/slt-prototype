import csv
import os
from os import path

import spacy
# from spacy import displacy
from gensim.models.keyedvectors import KeyedVectors


from slt.synonyms import WordnetSynonymExtractor

MIN_SIMILARITY = 0.2

WORDNET_DB_PATH = os.environ.get(
    "WORDNET_DB_PATH",
    path.expanduser("~/.local/share/models/wnjpn.db")
)
W2V_MODEL_PATH = os.environ.get(
    "W2V_MODEL_PATH",
    path.expanduser("~/.local/share/models/cc.ja.300.bin")
)
JAPANESE_MODEL = os.environ.get("JAPANESE_MODEL", "ja_core_news_sm")
JLPT_WORDS_PATH = os.environ.get("JLPT_WORDS_PATH", "../data/jlpt-vocab.csv")


class Parser:
    def __init__(self, synonyms_extractor, w2v, nlp, jlpt_words):
        self.synonyms_extractor = synonyms_extractor
        self.w2v = w2v
        self.nlp = nlp
        self.jlpt_words = jlpt_words

    def get_similarity(self, w1, w2):
        if w1 in self.w2v and w2 in self.w2v:
            return self.w2v.similarity(w1, w2)
        return 0.0

    def get_sorted_synonyms(self, word, max_word_level=0):
        result = []
        for candidate in self.synonyms_extractor.find_synonyms(word, n=-1):
            candidate_level = self.jlpt_words.get(candidate, 1)
            if candidate_level <= max_word_level:
                continue
            similarity = self.get_similarity(word, candidate)
            result.append((candidate, candidate_level, similarity))
        return sorted(result, key=lambda x: -x[1])

    def compute_token(self, token):
        word = token.text
        if token.pos_ != 'NOUN' or not token.tag_.endswith('一般'):
            return word
        word_level = self.jlpt_words.get(word, 1)
        synonyms = self.get_sorted_synonyms(word, max_word_level=word_level)
        for synonym, _level, similarity in synonyms:
            if similarity >= MIN_SIMILARITY:
                return synonym
        return word

    def process_sentence(self, sentence):
        doc = self.nlp(sentence)
        old_tokens = [token.text for token in doc]
        new_tokens = []
        for token in doc:
            # print(token.text, token.lemma_, token.dep_, token.pos_, token.tag_)
            new_tokens.append(self.compute_token(token))
        return new_tokens, old_tokens

    @classmethod
    def load(cls,
             wordnet_db_path=WORDNET_DB_PATH,
             w2v_model_path=W2V_MODEL_PATH,
             japanese_model=JAPANESE_MODEL,
             jlpt_words_path=JLPT_WORDS_PATH,
             w2v=None):
        synonyms_extractor = WordnetSynonymExtractor.load(wordnet_db_path)
        if w2v is None:
            w2v = KeyedVectors.load_word2vec_format(w2v_model_path, binary=True)
        nlp = spacy.load(japanese_model)
        with open(jlpt_words_path) as f:
            jlpt_words = {row['word']: int(row['level']) for row in csv.DictReader(f)}
        return cls(synonyms_extractor, w2v, nlp, jlpt_words)


# parser = Parser.load()
# new_tokens, old_tokens = parser.process_sentence("ご希望の日付を選択して下さい")
