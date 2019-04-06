MarkovBot
=========

MarkovBot is an IRC bot that, given a source text (imported into a SQLite3
database), uses a pseudorandom algorithm for synthesizing replies based on
phrases occurring in the source text.

**TODO:** Installation/usage documentation needs to be rewritten for the newest
version.  It'd also be nice to add an explanation of the design of the database
schema and algorithm changes.

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
