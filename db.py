import random
import sqlite3
import time

DELIM = '\ueeee'
PROFILE = False

def dbg(t, methodname, args):
    print('%s(%s): %.2f sec' % (methodname, ','.join(args), t))

def profile(f):
    if PROFILE:
        def fn(*args):
            start = time.perf_counter()
            res = f(*args)
            end = time.perf_counter()
            dbg(end - start, f.__name__, map(str, args[1:]))
            return res
        return fn
    else:
        return f

class MarkovDB:
    def __init__(self, dbname, k):
        self.conn = sqlite3.connect(dbname)
        self.k = k

    def create_tables(self):
        cur = self.conn.cursor()
        ddl = [
                '''
                CREATE TABLE IF NOT EXISTS heads (
                    head_id INTEGER PRIMARY KEY,
                    val TEXT COLLATE NOCASE,
                    occurrences INTEGER
                )
                ''',
                '''
                CREATE UNIQUE INDEX IF NOT EXISTS
                    u_heads_val
                ON
                    heads (val)
                ''',
                '''
                CREATE TABLE IF NOT EXISTS tails (
                    tail_id INTEGER PRIMARY KEY,
                    val TEXT COLLATE NOCASE
                )
                ''',
                '''
                CREATE UNIQUE INDEX IF NOT EXISTS
                    u_tails_val
                ON
                    tails (val)
                ''',
                '''
                CREATE TABLE IF NOT EXISTS chains (
                    head_id INTEGER,
                    tail_id INTEGER,
                    occurrence INTEGER,
                    FOREIGN KEY (head_id) REFERENCES heads (head_id),
                    FOREIGN KEY (tail_id) REFERENCES tails (tail_id)
                )
                ''',
                '''
                CREATE INDEX IF NOT EXISTS
                    i_chains_head_id_occurrence
                ON
                    chains (head_id, occurrence)
                '''
        ]

        for stmt in ddl:
            cur.execute(stmt)

    def insert(self, chain):
        if len(chain) != self.k + 1:
            raise RuntimeError('Expected chain to be a %d-tuple' % (self.k+1))

        head = chain[:-1]
        head_val = DELIM.join(head)
        tail = chain[-1]

        cur = self.conn.cursor()
        self._insert_head(cur, head_val)
        self._insert_tail(cur, tail)
        self._insert_chain(cur, head_val, tail)

    def _insert_head(self, cur, head_val):
        cur.execute(
                '''
                UPDATE heads
                SET occurrences = occurrences + 1
                WHERE val = ?
                ''',
                (head_val,)
        )

        if cur.rowcount == 0:
            cur.execute(
                    '''
                    INSERT INTO heads (
                        val, occurrences
                    ) VALUES (
                        ?, 1
                    )
                    ''',
                    (head_val,)
            )

    def _insert_tail(self, cur, tail):
        cur.execute(
                '''
                INSERT OR IGNORE INTO tails (
                    val
                ) VALUES (
                    ?
                )
                ''',
                (tail,)
        )

    def _insert_chain(self, cur, head_val, tail):
        cur.execute(
                '''
                SELECT head_id, occurrences
                FROM heads
                WHERE val = ?
                ''',
                (head_val,)
        )
        (head_id, occurrences) = list(cur)[0]

        cur.execute(
                '''
                SELECT tail_id
                FROM tails
                WHERE val = ?
                ''',
                (tail,)
        )
        tail_id, = list(cur)[0]

        cur.execute(
                '''
                INSERT INTO chains (
                    head_id,
                    tail_id,
                    occurrence
                ) VALUES (
                    ?,
                    ?,
                    ?
                )
                ''',
                (head_id, tail_id, occurrences - 1)
        )

    @profile
    def find_heads(self, possible_heads):
        substitutions = ['?' for head in possible_heads]
        possible_heads = map(
                lambda h: DELIM.join(h),
                possible_heads
        )

        cur = self.conn.cursor()
        cur.execute(
                f'''
                SELECT val
                FROM heads
                WHERE val IN ({','.join(substitutions)})
                ''',
                tuple(possible_heads)
        )

        return [val.split(DELIM) for val, in cur]

    @profile
    def heads_starting_with(self, start_word):
        start = start_word + DELIM
        end = start_word[:-1] + chr(ord(start_word[-1]) + 1) + DELIM

        cur = self.conn.cursor()
        cur.execute(
                '''
                SELECT val
                FROM heads
                WHERE val >= ?
                AND val < ?
                ''',
                (start, end)
        )

        return [val.split(DELIM) for val, in cur]

    @profile
    def random_head(self):
        cur = self.conn.cursor()
        cur.execute(
                '''
                SELECT val
                FROM heads
                WHERE rowid = (
                    ABS(RANDOM()) % (SELECT MAX (rowid) FROM heads)
                )
                '''
        )

        for val, in cur:
            return val.split(DELIM)

    @profile
    def random_tail(self):
        cur = self.conn.cursor()
        cur.execute(
                '''
                SELECT val
                FROM tails
                WHERE rowid = (
                    ABS(RANDOM()) % (SELECT MAX (rowid) FROM tails)
                )
                '''
        )

        for val, in cur:
            return val.split(DELIM)

    @profile
    def random_tail_following(self, head):
        head_val = DELIM.join(head)

        cur = self.conn.cursor()
        cur.execute(
                '''
                SELECT
                    tail.val
                FROM
                    heads AS head,
                    tails AS tail,
                    chains AS chain
                WHERE
                    head.head_id = chain.head_id
                AND tail.tail_id = chain.tail_id
                AND chain.occurrence =
                    (ABS(RANDOM()) % head.occurrences)
                AND head.val = ?
                ''',
                (head_val,)
        )

        for val, in cur:
            return val
