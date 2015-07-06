#!/usr/bin/python3

import sqlite3
import io
import json
import time

def init(c, k):
    c.execute("""CREATE TABLE IF NOT EXISTS chains
            (head TEXT COLLATE NOCASE, next TEXT COLLATE NOCASE, count INTEGER,
             PRIMARY KEY (head, next))""")
    c.execute("CREATE INDEX IF NOT EXISTS chains_head ON chains (head)")
    c.execute("""CREATE TABLE IF NOT EXISTS meta
            (key TEXT, value TEXT, PRIMARY KEY (key))""")
    c.execute("INSERT INTO meta VALUES ('k', ?)", (str(k),))

def generate(c, wordlist, k):
    lists = [wordlist[i:] for i in range(k + 1)]
    for words in zip(*lists):
        head = words[:k]
        next = words[k]

        c.execute("UPDATE chains SET count=count+1 WHERE head=? AND next=?",
                (str(head), next))
        if c.rowcount == 0:
            c.execute("INSERT INTO chains VALUES (?, ?, 1)",
                    (str(head), next))

if __name__ == "__main__":
    from sys import argv, exit, stdin
    if len(argv) != 3:
        print("Usage: {} <output db> <k>".format(argv[0]))
        exit(1)

    _, dbname, k = argv
    k = int(k)

    from config import name
    name_with_brackets = "<" + name + ">"

    conn = sqlite3.connect(dbname)
    init(conn, k)
    c = conn.cursor()

    lastk = []
    i = 0
    start = time.time()
    for line in io.TextIOWrapper(stdin.buffer, encoding="utf-8", errors="replace"):
        line = line.split()
        if len(line) == 0 or line[1] == "***" or line[1] == name_with_brackets:
            continue

        words = lastk + line[2:]
        generate(c, words, k)
        lastk = words[len(words)-k:]
        i += 1
        if i % 1000 == 0:
            conn.commit()
            print("1000 lines in " + str(time.time() - start) + "s")
            start = time.time()

    print("Flushing database writes...", end="")
    conn.commit()
    print("done")
