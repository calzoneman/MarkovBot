#!/usr/bin/python3

import argparse
from db import MarkovDB
import sys
import time

def import_file(db, f):
    k = db.k
    context = []
    i = 0
    start = time.perf_counter()

    for line in f:
        sentence = context + line.split()
        sublists = [sentence[i:] for i in range(k+1)]

        for chain in zip(*sublists):
            db.insert(chain)

        context = sentence[len(sentence)-k:]

        i += 1
        if i % 1000 == 0:
            db.conn.commit()
            print('1000 lines imported in %.2fs (total: %d lines)' % (
                (time.perf_counter() - start), i
            ))
            start = time.perf_counter()

    db.conn.commit()

def main():
    parser = argparse.ArgumentParser(
            description='Import text files into a MarkovBot database'
    )
    parser.add_argument(
            '-d', '--db',
            required=True,
            type=str,
            help='Filename for the SQLite3 database to write to'
    )
    parser.add_argument(
            '-k', '--context-size',
            required=True,
            type=int,
            help='Number of context words to store as the head of each chain'
    )
    parser.add_argument(
            'input',
            type=argparse.FileType('r', encoding='utf-8', errors='replace'),
            help='Input text file, or "-" to read from STDIN'
    )

    args = parser.parse_args(sys.argv[1:])

    db = MarkovDB(args.db, k=args.context_size)
    db.create_tables()

    with args.input:
        import_file(db, args.input)

if __name__ == '__main__':
    main()
