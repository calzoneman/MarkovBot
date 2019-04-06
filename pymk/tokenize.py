from . import Link

def iterate_words(lines):
    for line in lines:
        words = line.split()
        if len(words) == 0:
            continue

        for word in words[:-1]:
            yield word, is_stop_word(word)
        yield words[-1], True # EOL is considered a stop word

def is_stop_word(word):
    return any(word.endswith(stopchar) for stopchar in '.;?!')

def tokenize(source, link_length):
    head = []
    end = []
    is_start = True
    words_iter = iterate_words(source)

    while len(head) < link_length - 1:
        word, is_end = next(words_iter)
        head += [word]
        end += [is_end]

    for word, is_end in iterate_words(source):
        yield Link(head, word, is_start, is_end)
        head = head[1:] + [word]
        # If the start of the current link is a stop word, the next link
        # is a starting link
        is_start = end[0]
        end = end[1:] + [is_end]
