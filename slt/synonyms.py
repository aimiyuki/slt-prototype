import sqlite3


class WordnetSynonymExtractor:
    SYNONYM_QUERY = """
        SELECT lemma FROM word w
        JOIN sense s ON w.wordid = s.wordid
        WHERE w.lang = ? AND w.lemma <> ? AND s.synset in (
                SELECT s2.synset
                FROM word w
                JOIN sense s ON w.wordid = s.wordid
                JOIN synset s2 ON s.synset = s2.synset
                WHERE w.lemma = ?
        )
        LIMIT ?
    """

    def __init__(self, db: sqlite3.Connection, lang: str):
        """Uses wordnet to find synonyms
        """
        self.db = db
        self.lang = lang

    def find_synonyms(self, word: str, n: int = 10):
        if n == -1:
            n = 10_000
        cursor = self.db.cursor()
        cursor.execute(self.SYNONYM_QUERY, (self.lang, word, word, n))
        return set(v[0] for v in cursor.fetchall())

    @classmethod
    def load(cls, db_path: str, lang: str = "jpn"):
        conn = sqlite3.connect(db_path)
        return cls(conn, lang)
