from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Status(Enum):
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"


@dataclass()
class Word:
    surface: str
    status: Status = Status.UNCHANGED


@dataclass()
class Sentence:
    words: List[Word] = field(default_factory=list)

    def append(self, word: Word):
        self.words.append(word)

    def __len__(self):
        return len(self.words)

    def __iter__(self):
        return iter(self.words)
