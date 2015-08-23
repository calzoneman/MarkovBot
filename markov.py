#!/usr/bin/python

from ast import literal_eval
import sqlite3
import random

class Markov:
    def __init__(self, c):
        self.c = c
        self.k = 0
        self.c.execute("SELECT * FROM meta WHERE key='k'")
        for _, k in self.c:
            self.k = int(k)
        if self.k == 0:
            raise RuntimeError("Database is missing `k` meta field")

    def random_row(self):
        self.c.execute("""SELECT * FROM chains WHERE rowid =
            (ABS(RANDOM()) % (SELECT MAX(rowid) FROM chains))""")

    def find_seed(self, word):
        lower = "('" + word + "'"
        upper = "('" + word[:-1] + chr(ord(word[-1]) + 1) + "'"
        self.c.execute("SELECT * FROM chains WHERE head >= ? AND head < ? "
                       "ORDER BY RANDOM() LIMIT 1", (lower, upper))
        for head, _, _ in self.c:
            return literal_eval(head)

        self.random_row()
        for head, _, _ in self.c:
            return literal_eval(head)

    def pick_random_seed(self, words):
        if len(words) == 0:
            self.random_row()
            for head, _, _ in self.c:
                return literal_eval(head)

        seeds = [str(tuple(words[i:i+self.k]))
                 for i in range(len(words) - self.k + 1)]
        self.c.execute("SELECT * FROM chains WHERE head IN (" +
                       ",".join(["?"] * len(seeds)) + ") "
                       "ORDER BY RANDOM() LIMIT 1", tuple(seeds))
        for head, _, _ in self.c:
            return literal_eval(head)
        return self.find_seed(random.choice(words))

    def random_next(self, seed):
        self.c.execute("SELECT * FROM chains WHERE head=?", (str(seed),))
        possible = []
        for _, n, count in self.c:
            possible += [n] * count

        if len(possible) == 0:
            self.random_row()
            _, n, _ = next(self.c)
            return n
        else:
            return random.choice(possible)

    def chain(self, length=50, seed=None):
        if not seed:
            self.random_row()
            seed, _, _ = next(self.c)
            seed = literal_eval(seed)

        output = [w for w in seed]
        while len(output) < length:
            n = self.random_next(seed)
            output.append(n)
            seed = seed[1:] + (n,)

        return " ".join(output)
