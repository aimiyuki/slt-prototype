import csv
from typing import List

from japaneseverbconjugator.JapaneseVerbFormGenerator import JapaneseVerbFormGenerator
from japaneseverbconjugator.constants.EnumeratedTypes import (
    Formality,
    Polarity,
    Tense,
    VerbClass,
)

from slt import settings, japanese


IRREGULAR_POS = set(["30", "34", "38", "42", "45", "47", "48", "52", "58"])


class VerbTense:
    NonPast = 1
    Past = 2  # (~ta)
    Conjunctive = 3  # (~te)
    Provisional = 4  # (~eba)
    Potential = 5
    Passive = 6
    Causative = 7
    CausativePassive = 8
    Volitional = 9
    Imperative = 10
    Conditional = 11  # (~tara)
    Alternative = 12  # (~tari)
    Continuative = 13  # (~i)


class Conjugator:
    def __init__(self):
        self.conjugator = JapaneseVerbFormGenerator()
        with open(settings.CONJUGATOR_DATA, newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            self.conjugator_data = sorted(reader, key=lambda x: -len(x["okuri"]))

        self.verbs = {}
        with open(settings.VERBS_PATH) as f:
            for verb in csv.DictReader(f):
                self.verbs.setdefault(verb["normalized"], {})
                if verb["form"] == "基本形":
                    self.verbs[verb["normalized"]]["type"] = verb["subpos2"]
                elif verb["form"] == "未然形":
                    self.verbs[verb["normalized"]]["root"] = verb["verb"]

    def detect_class(self, verb: str, lemma: str):
        verb_info = self.verbs.get(lemma)
        if verb_info and verb_info["type"] == "一段":
            verb = verb[len(verb_info["root"]) :]
        for datum in self.conjugator_data:
            if verb.endswith(datum["okuri"]):
                conj = datum
                break
        else:
            return False
        return {
            "formality": Formality.POLITE if conj["fml"] == "t" else Formality.PLAIN,
            "polarity": Polarity.NEGATIVE if conj["neg"] == "t" else Polarity.POSITIVE,
            "tense": int(conj["conj"]),
        }

    def adjust_conjugation(
        self, source_verb: str, source_lemmas: List[str], target_verb: str
    ):
        print(source_verb, source_lemmas, target_verb)
        if not japanese.has_hiragana(target_verb) and "する" in source_lemmas:
            # both verbs are noun+する, simply: append the same ending
            return target_verb + source_verb.replace(source_lemmas[0], "")
        suffix = ""

        if source_verb.endswith("が"):
            suffix = source_verb[-1]
            source_verb = source_verb[:-1]

        if source_verb.endswith("ら") or source_verb.endswith("り"):
            suffix = source_verb[-1] + suffix
            source_verb = source_verb[:-1]
        conjugated = source_verb
        conj = self.detect_class(source_verb, source_lemmas[0])
        if not conj:
            return target_verb
        tense, formality, polarity = (
            conj["tense"],
            conj["formality"],
            conj["polarity"],
        )

        verb_info = self.verbs.get(target_verb)
        if not verb_info:
            return target_verb

        if verb_info["type"] == "一段":
            verb_class = VerbClass.ICHIDAN
        elif verb_info["type"].startswith("五段"):
            verb_class = VerbClass.GODAN
        else:
            verb_class = VerbClass.IRREGULAR

        args = [target_verb, verb_class, formality, polarity]
        if tense in [VerbTense.NonPast, VerbTense.Past]:
            if formality == Formality.PLAIN:
                func = self.conjugator.generate_plain_form
            else:
                func = self.conjugator.generate_polite_form
            conjugated = func(
                target_verb,
                verb_class,
                Tense.PAST if tense == VerbTense.Past else Tense.NONPAST,
                polarity,
            )
        elif tense == VerbTense.Conjunctive:
            conjugated = self.conjugator.generate_te_form(target_verb, verb_class)
        elif tense == VerbTense.Provisional:
            conjugated = self.conjugator.generate_provisional_form(*args)
        elif tense == VerbTense.Potential:
            conjugated = self.conjugator.generate_potential_form(*args)
        elif tense == VerbTense.Passive:
            conjugated = self.conjugator.generate_passive_form(*args)
        elif tense in [VerbTense.Causative, VerbTense.CausativePassive]:
            conjugated = self.conjugator.generate_causative_form(*args)
        elif tense == VerbTense.Volitional:
            conjugated = self.conjugator.generate_volitional_form(*args)
        elif tense == VerbTense.Imperative:
            conjugated = self.conjugator.generate_imperative_form(*args)
        elif tense == VerbTense.Conditional:
            conjugated = self.conjugator.generate_conditional_form(*args)
        return conjugated + suffix
