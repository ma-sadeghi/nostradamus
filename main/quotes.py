"""A small repository of tasteful quotes shown (at random) in the footer-ish
prophecy line. Poets, scientists and a couple of knowing winks about the folly
of predicting the future."""

import secrets

QUOTES = [
    {
        "text": "The first principle is that you must not fool yourself — and you are the easiest person to fool.",
        "author": "Richard Feynman",
    },
    {
        "text": "Yesterday I was clever, so I wanted to change the world. Today I am wise, so I am changing myself.",
        "author": "Rumi",
    },
    {"text": "Imagination is more important than knowledge.", "author": "Albert Einstein"},
    {
        "text": "It is difficult to make predictions, especially about the future.",
        "author": "Niels Bohr",
    },
    {
        "text": "Somewhere, something incredible is waiting to be known.",
        "author": "Carl Sagan",
    },
    {
        "text": "Nothing in life is to be feared, it is only to be understood.",
        "author": "Marie Curie",
    },
    {
        "text": "You were born with wings, why prefer to crawl through life?",
        "author": "Rumi",
    },
    {
        "text": "I would rather have questions that can't be answered than answers that can't be questioned.",
        "author": "Richard Feynman",
    },
    {
        "text": "Look deep into nature, and then you will understand everything better.",
        "author": "Albert Einstein",
    },
    {
        "text": "The cure for boredom is curiosity. There is no cure for curiosity.",
        "author": "Dorothy Parker",
    },
    {
        "text": "An investment in knowledge pays the best interest.",
        "author": "Benjamin Franklin",
    },
    {"text": "The best way to predict the future is to invent it.", "author": "Alan Kay"},
    {
        "text": "What we know is a drop, what we don't know is an ocean.",
        "author": "Isaac Newton",
    },
    {
        "text": "The good thing about science is that it's true whether or not you believe in it.",
        "author": "Neil deGrasse Tyson",
    },
    {"text": "Sell your cleverness and buy bewilderment.", "author": "Rumi"},
    {"text": "Study the past if you would define the future.", "author": "Confucius"},
    {
        "text": "The important thing is not to stop questioning.",
        "author": "Albert Einstein",
    },
    {"text": "Everything you can imagine is real.", "author": "Pablo Picasso"},
    {"text": "Stay hungry, stay foolish.", "author": "Whole Earth Catalog"},
    {
        "text": "We are just an advanced breed of monkeys on a minor planet of a very average star. But we can understand the universe. That makes us something very special.",
        "author": "Stephen Hawking",
    },
    {
        "text": "The present is theirs; the future, for which I really worked, is mine.",
        "author": "Nikola Tesla",
    },
    {
        "text": "Out beyond ideas of wrongdoing and rightdoing, there is a field. I'll meet you there.",
        "author": "Rumi",
    },
    {
        "text": "If you want to find the secrets of the universe, think in terms of energy, frequency and vibration.",
        "author": "Nikola Tesla",
    },
    {
        "text": "Logic will get you from A to B. Imagination will take you everywhere.",
        "author": "Albert Einstein",
    },
    {
        "text": "I have no special talent. I am only passionately curious.",
        "author": "Albert Einstein",
    },
    {
        "text": "Doubt is not a pleasant condition, but certainty is absurd.",
        "author": "Voltaire",
    },
    {
        "text": "The journey of a thousand miles begins with a single step.",
        "author": "Lao Tzu",
    },
    {
        "text": "Everything should be made as simple as possible, but not simpler.",
        "author": "Albert Einstein",
    },
    {"text": "Wisdom begins in wonder.", "author": "Socrates"},
    {"text": "You miss 100% of the shots you don't take.", "author": "Wayne Gretzky"},
]


def random():
    """Returns a randomly chosen quote dict ({"text", "author"})."""
    return secrets.choice(QUOTES)
