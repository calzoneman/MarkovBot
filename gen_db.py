#!/usr/bin/python3

from db import MarkovDB
import io
import time

def generate(db, wordlist, k):
    lists = [wordlist[i:] for i in range(k + 1)]
    for words in zip(*lists):
        db.insert(words)

if __name__ == "__main__":
    from sys import argv, exit, stdin
    if len(argv) != 3:
        print("Usage: {} <output db> <k>".format(argv[0]))
        exit(1)

    _, dbname, k = argv
    k = int(k)

    from config import nick
    name_with_brackets = "<" + nick + ">"

    db = MarkovDB(dbname, k)
    db.create_tables()

    lastk = []
    i = 0
    start = time.time()
    for line in io.TextIOWrapper(stdin.buffer, encoding="utf-8", errors="replace"):
        line = line.split()
        if len(line) == 0 or line[1] == "***" or line[1] == name_with_brackets:
            continue

        words = lastk + line[2:]
        generate(db, words, k)
        lastk = words[len(words)-k:]
        i += 1
        if i % 1000 == 0:
            db.conn.commit()
            print("1k lines in %.2fs (tot: %d)" % (time.time() - start, i))
            #print("1000 lines in " + str(time.time() - start) + "s")
            start = time.time()

    print("Flushing database writes...", end="")
    db.conn.commit()
    print("done")
