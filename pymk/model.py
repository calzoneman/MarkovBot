from collections import namedtuple

Link = namedtuple('Link', ['head', 'tail', 'is_start', 'is_end'])
Namespace = namedtuple('Namespace', ['link_length'])
