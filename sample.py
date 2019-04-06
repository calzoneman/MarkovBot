#!/usr/bin/python3

import argparse
import pymk
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
            '-t', '--target-min-length',
            type=int,
            help='Target minimum length of chain to generate'
    )
    parser.add_argument(
            '-m', '--max-length',
            required=True,
            type=int,
            help='Maximum length of chain to generate'
    )
    parser.add_argument(
            'prefix',
            type=str,
            nargs='*',
            help='Prefix (or exact match) to use as the start seed'
    )

    args = parser.parse_args(sys.argv[1:])

    db = pymk.SQLiteDB(args.db)
    with db.session() as session:
        ns = session.get_namespace()

        words = pymk.generate(session, ns, prefix=args.prefix,
                max_length=args.max_length,
                target_min_length=args.target_min_length)

        if len(words) == 0:
            print('(No results)')
        else:
            print(' '.join(words))

if __name__ == '__main__':
    main()
