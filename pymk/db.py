import contextlib
import random
import sqlite3

from . import Link, Namespace

delimiter = '\ueeee'

class SQLiteDB:
    def __init__(self, path):
        self._path = path

    @contextlib.contextmanager
    def session(self):
        with sqlite3.connect(self._path) as conn:
            yield _session(conn)

class _session:
    def __init__(self, conn):
        self._conn = conn
        self._conn.cursor().execute('PRAGMA synchronous = NORMAL;')

    def get_namespace(self):
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT link_length FROM markov_metadata
        ''')

        rows = cursor.fetchall()
        if len(rows) == 0:
            raise Exception('Missing markov_metadata entry')
        elif len(rows) > 1:
            raise Exception('Duplicate markov_metadata entry')

        return Namespace(rows[0][0])

    def create_links(self, links):
        for link in links:
            self._insert_link(link)

        self._conn.commit()

    def _insert_link(self, link):
        is_start = 'Y' if link.is_start else 'N'
        is_end = 'Y' if link.is_end else 'N'

        self._conn.cursor().execute('''
            INSERT INTO links (
                head_val,
                tail_val,
                is_start,
                is_end
            ) VALUES (
                ?,
                ?,
                ?,
                ?
            )''', (delimiter.join(link.head), link.tail, is_start, is_end))

    def head_with_prefix(self, prefix, require_start=False):
        start = delimiter.join(prefix)
        end = start[:-1] + chr(ord(start[-1]) + 1)

        query = '''
            SELECT head_val
              FROM links
             WHERE head_val >= ?
               AND head_val < ?
        '''

        if require_start:
            query += ''' AND is_start = 'Y' '''

        cursor = self._conn.cursor()
        cursor.execute(query, (start, end))

        choices = cursor.fetchall()

        if len(choices) == 0:
            return None

        return random.choice(choices)[0].split(delimiter)

    def random_head(self):
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT link.head_val
              FROM start_links sl,
                   links link
             WHERE link.rowid = sl.link_rowid
               AND sl.rowid = (
                     ABS(RANDOM()) % (SELECT MAX (rowid) FROM start_links)
                   )
        ''')
        val, = cursor.fetchone()
        return val.split(delimiter)

    def random_link(self, head):
        head_val = delimiter.join(head)
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT tail_val,
                   is_start,
                   is_end
              FROM links
             WHERE head_val = ?
               AND occurrence = (
                     ABS(RANDOM()) % (SELECT num_occurrences FROM heads WHERE head_val = ?)
                   )
        ''', (head_val, head_val))

        row = cursor.fetchone()
        if row is None:
            return None

        tail_val, is_start, is_end = row
        return Link(head, tail_val, is_start == 'Y', is_end == 'Y')
