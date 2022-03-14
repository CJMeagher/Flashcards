import io
import json
import logging
import random
from collections import namedtuple
import argparse


Flashcard = namedtuple("Flashcard", "term definition")


class Deck:
    def __init__(self, json_deck=None):
        self.term_to_definition = {}
        self.definition_to_term = {}
        self.term_to_mistakes = {}
        if json_deck:
            self.import_deck(json_deck)

    def __repr__(self):
        deck_json, _ = self.export_deck()
        return f"Deck({deck_json})"

    def __str__(self):
        deck_string = self.get_all_cards()
        return deck_string

    def __len__(self):
        return len(self.term_to_definition)

    def get_by_term(self, term):
        try:
            return Flashcard(term, self.term_to_definition[term])
        except KeyError:
            raise KeyError

    def get_by_definition(self, definition):
        try:
            return Flashcard(self.definition_to_term[definition], definition)
        except KeyError:
            raise KeyError

    def get_all_cards(self):
        all_cards = [
            Flashcard(term, definition)
            for term, definition in self.term_to_definition.items()
        ]
        return all_cards

    def get_random_card(self):
        choice = random.choice(list(self.term_to_definition.items()))
        return Flashcard(*choice)

    def insert_card(self, flashcard):
        if (flashcard.term in self.term_to_definition) or (
            flashcard.definition in self.definition_to_term
        ):
            raise KeyError(f"Duplicate term or definition: {flashcard}")
        self.term_to_definition[flashcard.term] = flashcard.definition
        self.definition_to_term[flashcard.definition] = flashcard.term
        self.term_to_mistakes[flashcard.term] = 0

    def remove_card(self, flashcard):
        try:
            del self.term_to_definition[flashcard.term]
            del self.term_to_mistakes[flashcard.term]
            del self.definition_to_term[flashcard.definition]
        except KeyError:
            raise KeyError

    def import_deck(self, json_string):
        # flashcards stored in json as - term: (definition, stats)
        # e.g. "France": ("Paris", 10)
        # this function splits into 3 dictionaries
        imported_deck = json_string
        old_term_to_definition = self.term_to_definition.copy()
        old_term_to_stats = self.term_to_mistakes.copy()

        self.term_to_definition = {
            term: definition for term, (definition, _) in imported_deck.items()
        }
        self.term_to_mistakes = {
            term: stats for term, (_, stats) in imported_deck.items()
        }
        self.definition_to_term = {
            definition: term for term, definition in self.term_to_definition.items()
        }

        for term, definition in old_term_to_definition.items():
            try:
                self.insert_card(Flashcard(term, definition))
                self.term_to_mistakes[term] = old_term_to_stats[term]
            except KeyError:
                pass

        return len(imported_deck)

    def export_deck(self):
        json_string = {}
        for term, definition in self.term_to_definition.items():
            stats = self.term_to_mistakes[term]
            json_string[term] = (definition, stats)
        cards_exported = len(self)
        return json_string, cards_exported

    def ask(self, flashcard, answer):

        if answer == flashcard.definition:
            return True, answer

        self.term_to_mistakes[flashcard.term] += 1
        try:
            term = self.definition_to_term[answer]
        except KeyError:
            term = None
        return False, term

    def get_hardest_cards(self):
        max_mistakes = max(self.term_to_mistakes.values(), default=0)
        if max_mistakes == 0:
            return [], 0
        hardest_cards = [
            term
            for term, mistakes in self.term_to_mistakes.items()
            if mistakes == max_mistakes
        ]
        return hardest_cards, max_mistakes

    def reset_stats(self):
        self.term_to_mistakes = dict.fromkeys(self.term_to_definition.keys(), 0)


class Session:

    def __init__(self, import_from=None, export_to=None):

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        self.log = io.StringIO()
        stream_handler = logging.StreamHandler(self.log)
        stream_log_format = "%(asctime)s | %(message)s"
        stream_handler.setFormatter(logging.Formatter(stream_log_format))
        stream_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(stream_handler)

        self.deck = Deck()
        if import_from:
            self._import(import_from)
        self.export_to = export_to

    def loop(self):
        actions = [
            "add",
            "remove",
            "import",
            "export",
            "ask",
            "exit",
            "log",
            "hardest card",
            "reset stats",
        ]
        while True:
            action = self.get_input_and_log(f"Input the action ({', '.join(actions)}):")
            try:
                eval(f"self._{action.replace(' ', '_')}()")
            except AttributeError:
                self.print_and_log("Invalid action!")

    def _add(self):
        term = self.get_input_and_log("The card:")
        while True:
            try:
                _ = self.deck.get_by_term(term)
                term = self.get_input_and_log(
                    f'The card "{term}" already exists. Try again:'
                )
            except KeyError:
                break
        definition = self.get_input_and_log("The definition of the card:")
        while True:
            try:
                _ = self.deck.get_by_definition(definition)
                definition = self.get_input_and_log(
                    f'The definition "{definition}" already exists. Try again:\n'
                )
            except KeyError:
                break

        new_card = Flashcard(term, definition)
        self.deck.insert_card(new_card)
        self.print_and_log(
            f'The pair ("{new_card.term}":"{new_card.definition}") has been added.'
        )
        print()

    def _remove(self):
        term = self.get_input_and_log("Which card?")
        try:
            flashcard = self.deck.get_by_term(term)
            self.deck.remove_card(flashcard)
            self.print_and_log(f"The card has been removed")
        except KeyError:
            self.print_and_log(f'Can\'t remove "{term}": there is no such card.')
        print()

    def _import(self, import_from=None):
        if import_from:
            file_name = import_from
        else:
            file_name = self.get_input_and_log("File name:")
        try:
            with open(file_name, "r") as in_file:
                json_deck = json.load(in_file)
            cards_imported = self.deck.import_deck(json_deck)
            self.print_and_log(f"{cards_imported} cards have been loaded.")
        except FileNotFoundError:
            self.print_and_log("File not found.")
        except Exception as e:
            self.logger.warning(e)
        print()

    def _export(self, export_to=None):
        if export_to:
            file_name = export_to
        else:
            file_name = self.get_input_and_log("File name:")
        json_string, cards_saved = self.deck.export_deck()
        with open(file_name, "w") as out_file:
            json.dump(json_string, out_file)
        self.print_and_log(f"{cards_saved} cards have been saved.")
        print()

    def _ask(self):

        if len(self.deck) == 0:
            self.print_and_log("There are no flashcards in the deck.")
            return

        while True:
            try:
                asks = int(self.get_input_and_log("How many times to ask?"))
                break
            except ValueError:
                self.print_and_log("Enter a number")

        for _ in range(asks):
            flashcard = self.deck.get_random_card()
            user_answer = self.get_input_and_log(
                f'Print the definition of "{flashcard.term}"'
            )
            is_correct, correct_term = self.deck.ask(flashcard, user_answer)
            if is_correct:
                self.print_and_log("Correct!")
            else:
                if correct_term:
                    rest_of_message = (
                        f', but your definition is correct for "{correct_term}".'
                    )
                else:
                    rest_of_message = "."
                self.print_and_log(
                    f'Wrong. The right answer is "{flashcard.definition}"{rest_of_message}'
                )

        print()

    def _exit(self):
        if self.export_to:
            self._export(self.export_to)
        self.print_and_log("Bye bye!")
        quit()

    def _log(self):
        file_name = self.get_input_and_log("File name:")
        with open(file_name, "w") as out_log:
            out_log.write(self.log.getvalue())
        self.print_and_log("The log has been saved.")
        print()

    def _hardest_card(self):
        terms, mistakes = self.deck.get_hardest_cards()
        terms_string = ", ".join([f'"{term}"' for term in terms])
        if len(terms) == 0:
            message = "There are no cards with errors."
        elif len(terms) == 1:
            message = f"The hardest card is {terms_string}. You have {mistakes} errors answering it."
        else:
            message = f"The hardest cards are {terms_string}. You have {mistakes} errors answering them."
        self.print_and_log(message)

    def _reset_stats(self):
        self.deck.reset_stats()
        self.print_and_log("Card statistics have been reset.")

    def get_input_and_log(self, message):
        self.logger.debug(message)
        print(message)
        response = input().strip()
        self.logger.debug(response)
        return response

    def print_and_log(self, message):
        self.logger.debug(message)
        print(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--import_from")
    parser.add_argument("--export_to")
    args = parser.parse_args()
    session = Session(args.import_from, args.export_to)
    session.loop()


if __name__ == "__main__":
    main()
