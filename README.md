MarkovBot
=========

MarkovBot is an IRC bot that, given a source text (imported into a SQLite3
database), uses a pseudorandom algorithm for synthesizing replies based on
phrases occurring in the source text.

## Installation

### Requirements

  * Python 3
  * `pip`/`virtualenv`

### Setup

```sh
$ virtualenv .env # Make sure this is Python 3's virtualenv
$ .env/bin/pip install requirements.txt
```

## Importing text

Use the provided `import.py` script:

    usage: import.py [-h] -d DB -k CONTEXT_SIZE input

    Import text files into a MarkovBot database

    positional arguments:
      input                 Input text file, or "-" to read from STDIN

    optional arguments:
      -h, --help            show this help message and exit
      -d DB, --db DB        Filename for the SQLite3 database to write to
      -k CONTEXT_SIZE, --context-size CONTEXT_SIZE
                            Number of context words to store as the head of each
                            chain

I find that passing `-k 2` (2 words of context) works pretty well.  A lower `k`
results in less intelligible output, a higher `k` tends towards reproducing the
input sentences verbatim.

The `k` value used to create the database must also be set in `config.py` for
the bot to load the database correctly.

You can check sample output by using the provided `sample.py` script.

## Launching

```sh
$ cp config.py.example config.py
$ $EDITOR config.py
$ .env/bin/python markovbot.py
```

## How it works

When importing text into the database, sentences are broken up into chains of
context phrases and following words based on the context size (`k`).

For example, using `k=2`, the phrase "Python is fun" would be represented as a
chain head containing "Python" and "is", and a following word "fun":

    +-------------+  +-----+
    |'Python'|'is'+-->'fun'|
    +-------------+  +-----+

When building up output, a sliding window with length `k` is used and each next
word is determined by selecting, at random, one chain starting with the context,
weighted by the relative frequency of the chain.

For example, if the database is created from the sentence "Python is fun Python
is fun Python is great", given the context "Python is", the algorithm will
choose "fun" as the next word approximately 2/3 of the time, and "great"
approximately 1/3 of the time.  The algorithm then shifts forward by one word
and considers chains beginning with "is fun" or "is great", depending on which
was picked.

    +-------------+  +-----+
    |'Python'|'is'+-->'fun'|   Relative Probability: 2
    +-------------+  +-----+

    +-------------+  +-------+
    |'Python'|'is'+-->'great'| Relative Probability: 1
    +-------------+  +-------+
