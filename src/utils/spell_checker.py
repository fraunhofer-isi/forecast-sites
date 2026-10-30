# SPDX-FileCopyrightText: 2026 Fraunhofer-Gesellschaft e.V., München
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# AI-assisted code generation was used during development.

from spellchecker import SpellChecker

spell = SpellChecker(language='en')

custom_words = [
    # Add your custom words here to extend the word list of SpellChecker
    'Salzgitter',
    'PyCharm',
    'sqlite3',
]

spell.word_frequency.load_words(custom_words)


def check(text):
    words = text.split()
    suggestions = {}
    for word in words:
        if word not in spell:
            suggestion = spell.correction(word)
            suggestions[word] = suggestion
    return suggestions
