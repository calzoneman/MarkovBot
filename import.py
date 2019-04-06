#!/usr/bin/python3

import argparse
import pymk
import sys
import time

def import_file(session, ns, f, batch_size=1000):
    links = []
    i = 0
    start = time.perf_counter()
    for link in pymk.tokenize(f, link_length=ns.link_length):
        links.append(link)
        i += 1
        if len(links) > batch_size:
            session.create_links(links[:batch_size])
            links = links[batch_size:]
            print('\r%d links imported in %.2fs (total: %d links)' % (
                batch_size, (time.perf_counter() - start), i
            ), end='')
            start = time.perf_counter()

    if len(links) > 0:
        session.create_links(links)

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
            '-b', '--batch-size',
            default=1000,
            type=int,
            help='Batch size to use for inserts'
    )
    parser.add_argument(
            'input',
            type=argparse.FileType('r', encoding='utf-8', errors='replace'),
            help='Input text file, or "-" to read from STDIN'
    )

    args = parser.parse_args(sys.argv[1:])

    db = pymk.SQLiteDB(args.db)
    with db.session() as session:
        ns = session.get_namespace()
        with args.input:
            import_file(session, ns, args.input, args.batch_size)

if __name__ == '__main__':
    main()
