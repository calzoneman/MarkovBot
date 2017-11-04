#!/usr/bin/python3

import argparse
from db import MarkovDB
from markov import Markov
import sys

def main():
    parser = argparse.ArgumentParser(
            description='Generate sample random chains from a '
                        'MarkovBot database'
    )
    parser.add_argument(
            '-d', '--db',
            required=True,
            type=str,
            help='Filename for the SQLite3 database to use'
    )
    parser.add_argument(
            '-k', '--context-size',
            required=True,
            type=int,
            help='Number of context words in the head of each chain'
    )
    parser.add_argument(
            '-l', '--length',
            required=True,
            type=int,
            help='Length of chain to generate'
    )

    args = parser.parse_args(sys.argv[1:])

    db = MarkovDB(args.db, k=args.context_size)
    markov = Markov(db)

    print(markov.chain(length=args.length))

if __name__ == '__main__':
    main()
