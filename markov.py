import random

class Markov:
    def __init__(self, source, k=5):
        self.source = source
        self.k = k
        self._init_source()

    def _init_source(self):
        self.seeds = {}
        for i in range(len(self.source) - self.k - 1):
            seed = tuple(self.source[i:i+self.k])
            if seed not in self.seeds:
                self.seeds[seed] = []
            self.seeds[seed].append(self.source[i+self.k])
        print('Markov dict initialized with {} keys'.format(len(self.seeds.keys())))

    def chain(self, length=50, seed=None):
        if not seed or seed not in self.seeds:
            seed = random.choice(list(self.seeds.keys()))
        output = []
        while len(output) < length:
            if seed not in self.seeds:
                seed = random.choice(list(self.seeds.keys()))
            next = random.choice(self.seeds[seed])
            output.append(next)
            seed = tuple(list(seed[1:]) + [next])
        return ' '.join(output)

    def find_seed(self, start_word):
        seeds = list(self.seeds.keys())
        seeds = list(filter(lambda s: start_word in s, seeds))
        if len(seeds) == 0:
            return None
        return random.choice(seeds)
