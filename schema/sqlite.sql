CREATE TABLE markov_metadata (
    link_length INTEGER CHECK (link_length > 1)
);

CREATE TABLE heads (
    head_val TEXT COLLATE NOCASE,
    num_occurrences INTEGER,
    PRIMARY KEY (head_val)
);

CREATE TABLE start_links (
    link_rowid INTEGER
);

CREATE UNIQUE INDEX u_start_links_link_rowid
    ON start_links (link_rowid);

CREATE TABLE links (
    head_val TEXT COLLATE NOCASE,
    tail_val TEXT COLLATE NOCASE,
    occurrence INTEGER,
    is_start CHAR(1) DEFAULT 'N' CHECK (is_start IN ('Y', 'N')),
    is_end CHAR(1) DEFAULT 'N' CHECK (is_end IN ('Y', 'N'))
);

CREATE TRIGGER tg_links_after_insert
AFTER INSERT ON links
FOR EACH ROW
BEGIN
    INSERT INTO heads (head_val, num_occurrences) VALUES (NEW.head_val, 1)
    ON CONFLICT (head_val) DO UPDATE SET num_occurrences = num_occurrences + 1;

    -- Assign unique occurrence ID to each link that begins with a given head
    -- for efficient look up by ABS(RANDOM()) % num_occurrences
    UPDATE links SET occurrence = (
                       SELECT num_occurrences - 1
                         FROM heads
                        WHERE head_val = NEW.head_val
                     )
     WHERE rowid = NEW.rowid;

    -- Build index table for random access to start links
    INSERT INTO start_links SELECT rowid
                              FROM links
                             WHERE rowid = NEW.rowid
                               AND is_start = 'Y';
END;

CREATE INDEX i_links_head_val_start
    ON links (head_val, is_start);
CREATE INDEX i_links_head_val_occurrence
    ON links (head_val, occurrence);
