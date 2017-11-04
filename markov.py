import random

class Markov:
    def __init__(self, db):
        self.db = db
        self.k = db.k

    def random_head(self, words):
        if len(words) == 1:
            heads = self.db.heads_starting_with(words[0])
            if len(heads) == 0:
                return self.db.random_head()

            return random.choice(heads)

        possible_heads = [
                words[i:i+self.k]
                for i in range(len(words) - self.k + 1)
        ]

        heads = self.db.find_heads(possible_heads)

        if len(heads) == 0:
            return self.db.random_head()

        return random.choice(heads)

    def random_tail(self, head):
        tail = self.db.random_tail_following(head)
        if tail is None:
            tail = self.db.random_tail()

        return tail

    def chain(self, length=50, head=None):
        if not head:
            head = self.db.random_head()

        output = [w for w in head]
        while len(output) < length:
            n = self.random_tail(head)
            output.append(n)
            head = head[1:] + [n]

        return " ".join(output)
