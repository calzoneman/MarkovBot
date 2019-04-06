def generate(db, ns, prefix=None, target_min_length=None, max_length=None):
    if max_length is None:
        raise Exception('Must provide max_length')
    if target_min_length is None:
        target_min_length = max_length

    if prefix is None or len(prefix) == 0:
        head = db.random_head()
    elif len(prefix) == ns.link_length - 1:
        head = prefix
    elif len(prefix) < ns.link_length - 1:
        head = db.head_with_prefix(prefix, require_start=True)
        if head is None:
            head = db.head_with_prefix(prefix, require_start=False)
        if head is None:
            head = db.random_head()
    else:
        raise ValueError('Mismatched prefix length')

    words = head[:]
    last_stop = None
    while len(words) < max_length:
        link = db.random_link(head)
        if link is None:
            break

        words += [link.tail]
        head = head[1:] + [link.tail]
        if link.is_end:
            last_stop = len(words)

    if len(words) < ns.link_length:
        return []

    if last_stop is not None and last_stop >= target_min_length:
        return words[:last_stop]

    return words
