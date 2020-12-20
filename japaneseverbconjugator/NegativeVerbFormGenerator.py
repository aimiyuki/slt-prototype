# Local modules
from .constants.ParticleConstants import *
from .constants.VerbEndingConstants import *
from .constants.EnumeratedTypes import Formality, Tense, VerbClass

from .Utils import *

# ---------------------------------------------------------- #
#                       Negative Verb Forms                  #
# ---------------------------------------------------------- #
class NegativeVerbForms:
    def generate_plain_form(self, verb, verb_class, tense):
        '''Generate the negative plain form of the verb depending
        on the tense.

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            tense (enum): Tense Enum representing the tense for the conjugated verb 

        Returns:
            str: negative plain form of the verb based on the tense
        parameter
        '''
        verb = generate_nai_form(verb, verb_class, True)
        if tense == Tense.NONPAST:
            return verb
        # force a non-irregular verb class to remove ending -i particle
        return "{}{}".format(splice_verb(verb, VerbClass.NONIRREGULAR), KATTA_ENDING)

    def generate_polite_form(self, verb, verb_class, tense):
        '''Generate the negative polite form of the verb depending
        on the tense.

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            tense (enum): Tense Enum representing the tense for the conjugated verb 

        Returns:
            str: negative polite form of the verb based on the tense
        parameter
        '''
        ending = MASU_NEGATIVE_PAST
        if tense == Tense.NONPAST:
            ending = MASU_NEGATIVE_NONPAST

        if verb_class == VerbClass.IRREGULAR:
            return handle_irregular_verb(verb, append_stem_particle=True, suru_ending=ending, kuru_ending=ending)
        else:
            verb_base = splice_verb(verb, verb_class)
            if verb_class == VerbClass.GODAN:
                verb_base = map_dictionary_to_i_ending(verb)
            # no change needed for ichidan verb
            return "{}{}".format(verb_base, ending)


    def generate_conditional_form(self, verb, verb_class, formality):
        '''Generate the negative conditional form of the verb depending
        on the formality.

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            formality (enum): Formality Enum representing the formality class
                for the conjugated verb 

        Returns:
            str: negative conditional form of the verb based on the formality
        parameter
        '''
        if formality == Formality.PLAIN:
            verb = self.generate_plain_form(verb, verb_class, Tense.PAST)
        else:
            verb = self.generate_polite_form(verb, verb_class, Tense.PAST)
        return "{}{}".format(verb, RA_PARTICLE)   

    def generate_volitional_form(self, verb, verb_class, formality):
        '''Generate the negative volitional form of the verb depending
        on the formality. 

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            formality (enum): Formality Enum representing the formality class
                for the conjugated verb 

        Returns:
            str: negative volitional form of the verb based on the formality
        parameter
        '''
        verb_nai_form = generate_nai_form(verb, verb_class, True)
        if formality == Formality.PLAIN:
            return "{}{}".format(verb_nai_form, VOLITIONAL_PLAIN_COPULA)
        elif formality == Formality.POLITE:
            return "{}{}".format(verb_nai_form, VOLITIONAL_POLITE_COPULA)

    def generate_potential_form(self, verb, verb_class, formality):
        '''Generate the negative potential form of the verb depending
        on the formality.

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            formality (enum): Formality Enum representing the formality class
                for the conjugated verb 

        Returns:
            str: negative potential form of the verb based on the formality
        parameter
        '''
        if verb_class == VerbClass.IRREGULAR:
            if formality == Formality.PLAIN:
                return handle_irregular_verb(verb, suru_ending=POTENTIAL_SURU_PLAIN_NEGATIVE_ENDING, kuru_ending=POTENTIAL_KURU_PLAIN_NEGATIVE_ENDING)
            else:
                return handle_irregular_verb(verb, suru_ending=POTENTIAL_SURU_POLITE_NEGATIVE_ENDING, kuru_ending=POTENTIAL_KURU_POLITE_NEGATIVE_ENDING)
        else:
            verb_base = map_dictionary_to_e_ending(verb)

            if verb_class == VerbClass.GODAN:
                if formality == Formality.PLAIN:
                    return generate_nai_form(verb_base, verb_class, False)
                else:
                    return "{}{}".format(verb_base, MASU_NEGATIVE_NONPAST)
            elif verb_class == VerbClass.ICHIDAN:
                verb_base = splice_verb(verb, verb_class)
                verb_with_rare = "{}{}".format(verb_base, "られ")
                if formality == Formality.PLAIN:
                    return generate_nai_form(verb_with_rare, verb_class, False)
                else:
                    return "{}{}".format(verb_with_rare, MASU_NEGATIVE_NONPAST)
    
    def generate_imperative_form(self, verb, verb_class, formality):
        '''Generate the negative imperative form of the verb depending
        on the formality.

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            formality (enum): Formality Enum representing the formality class
                for the conjugated verb 

        Returns:
            str: negative imperative form of the verb based on the formality
        parameter
        '''
        if verb_class == VerbClass.IRREGULAR:
            if formality == Formality.PLAIN:
                return handle_irregular_verb(verb, suru_ending="{}{}".format(SURU_ENDING, NA_PARTICLE), kuru_ending="{}{}".format(KURU_ENDING, NA_PARTICLE))
            else:
                nai_form = generate_nai_form(verb, verb_class, True)
                return "{}{}{}".format(nai_form, DE_PARTICLE, KUDASAI)
        else:
            if formality == Formality.PLAIN:
                return "{}{}".format(verb, NA_PARTICLE)
            else:
                return "{}{}{}".format(generate_nai_form(verb, verb_class, True), DE_PARTICLE, KUDASAI)
    
    def generate_provisional_form(self, verb, verb_class, formality):
        '''Generate the negative provisional form of the verb depending
        on the formality.

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            formality (enum): Formality Enum representing the formality class
                for the conjugated verb 

        Returns:
            str: negative provisional form of the verb based on the formality
        parameter
        '''
        if verb_class == VerbClass.IRREGULAR:
            if formality == Formality.PLAIN:
                if splice_verb(verb, verb_class, False) == SURU_ENDING:
                    return handle_irregular_verb(verb, append_stem_particle=True, suru_ending=PROVISIONAL_ICHIDAN_PLAIN_NEGATIVE_ENDING)
                else:
                    return "{}{}".format(KO_PARTICLE, PROVISIONAL_ICHIDAN_PLAIN_NEGATIVE_ENDING)
            else:
                intermediate_verb = handle_irregular_verb(verb, append_stem_particle=True, suru_ending=MASU_NEGATIVE_NONPAST, kuru_ending=MASU_NEGATIVE_NONPAST)
                return "{}{}{}".format(intermediate_verb, NA_PARTICLE, RA_PARTICLE)
        else:
            verb_stem = splice_verb(verb, verb_class)
            if verb_class == VerbClass.GODAN:
                verb_with_a_ending = map_dictionary_to_a_ending(verb)
                return "{}{}".format(verb_with_a_ending, PROVISIONAL_ICHIDAN_PLAIN_NEGATIVE_ENDING)
            elif verb_class == VerbClass.ICHIDAN:
                return "{}{}".format(verb_stem, PROVISIONAL_ICHIDAN_PLAIN_NEGATIVE_ENDING)
    

    def generate_causative_form(self, verb, verb_class, formality):
        '''Generate the negative causative form of the verb depending
        on the formality.

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            formality (enum): Formality Enum representing the formality class
                for the conjugated verb 

        Returns:
            str: negative causative form of the verb based on the formality
        parameter
        '''
        if verb_class == VerbClass.IRREGULAR:
            if splice_verb(verb, verb_class, False) != SURU_ENDING:
                if formality == Formality.PLAIN: 
                    return generate_nai_form(CAUSATIVE_KURU_NEGATIVE_BASE, verb_class, False)
                else:
                    return "{}{}".format(CAUSATIVE_KURU_NEGATIVE_BASE, MASU_NEGATIVE_NONPAST)
        else:
            verb_stem = splice_verb(verb, verb_class)
            if verb_class == VerbClass.GODAN:
                modified_verb_stem = "{}{}".format(map_dictionary_to_a_ending(verb), SE_PARTICLE)
                if formality == Formality.PLAIN:
                    return generate_nai_form(modified_verb_stem, verb_class, False)
                else:
                    return "{}{}".format(modified_verb_stem, MASU_NEGATIVE_NONPAST)
            elif verb_class == VerbClass.ICHIDAN:
                modified_verb_stem = "{}{}{}".format(verb_stem, SA_PARTICLE, SE_PARTICLE)
                if formality == Formality.PLAIN:
                    return generate_nai_form(modified_verb_stem, verb_class, False)
                else:
                    return "{}{}".format(modified_verb_stem, MASU_NEGATIVE_NONPAST)

    def generate_passive_form(self, verb, verb_class, formality):
        '''Generate the negative passive form of the verb depending
        on the formality.

        Args:
            verb (str): Japanese verb in kana, might contain kanji
            verb_class (enum): VerbClass Enum representing the verb class
                to which the verb belongs
            formality (enum): Formality Enum representing the formality class
                for the conjugated verb 

        Returns:
            str: negative passive form of the verb based on the formality
        parameter
        '''
        if verb_class == VerbClass.GODAN:
            verb_with_updated_ending = "{}{}".format(map_dictionary_to_a_ending(verb), RE_PARTICLE)
            if formality == Formality.PLAIN:
                return generate_nai_form(verb_with_updated_ending, verb_class, False)
            else:
                return "{}{}".format(verb_with_updated_ending, MASU_NEGATIVE_NONPAST)
        elif verb_class == VerbClass.ICHIDAN:
            modified_verb_stem = "{}{}{}".format(splice_verb(verb, verb_class), RA_PARTICLE, RE_PARTICLE)
            if formality == Formality.PLAIN:
                return generate_nai_form(modified_verb_stem, verb_class, False)
            else:
                return "{}{}".format(modified_verb_stem, MASU_NEGATIVE_NONPAST)
