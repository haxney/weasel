#!/usr/bin/env python

from __future__ import division

import random
import string
import sys
import argparse
import difflib
import collections

# From https://secure.wikimedia.org/wikibooks/en/wiki/Algorithm_implementation/Strings/Levenshtein_distance#Python
def levenshtein(s1, s2):
    """Calculate the Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if not s1:
        return len(s2)

    previous_row = xrange(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def match_to_ratio(matcher, s1, s2, inverse=True):
    """Turns a number of matched characters into a ratio.

    Calls matcher(s1, s2), and divides the number of matched characters by the
    length of the longer string. This produces a "ratio" of matched characters,
    which will be 1.0 if s1 == s2.

    If `invert` is False, then assume that the number returned from matcher() is
    the number of matching characters, rather than the number of non-matching
    characters (the default)."""
    return abs(matcher(s1, s2) / max(len(s1), len(s2)) - inverse)

def levenshtein_fitness(s1, s2):
    """Calculate fitness based on Levenshtein distance.
    Returns a float in the range [0.0, 1.0]."""
    return match_to_ratio(levenshtein, s1, s2)

def sequence_matcher_fitness(s1, s2):
    """Use SequenceMatcher.ratio() to get a fitness distance."""
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def matching_blocks_fitness(s1, s2):
    """Use SequenceMatcher.get_matching_blocks() to get a fitness."""
    def matcher(a, b):
        return sum(map(lambda i: i[2], difflib.SequenceMatcher(None, a, b).get_matching_blocks()))

    return match_to_ratio(matcher, s1, s2, False)

# From http://stackoverflow.com/questions/2892931
def long_substr(*strings):
    substr = ''
    if len(strings) > 1 and len(strings[0]) > 0:
        for i in range(len(strings[0])):
            for j in range(len(strings[0])-i+1):
                if j > len(substr) and is_substr(strings[0][i:i+j], strings):
                    substr = strings[0][i:i+j]
    return substr

def is_substr(find, data):
    if len(data) < 1 and len(find) < 1:
        return False
    for i in range(len(data)):
        if find not in data[i]:
            return False
    return True

def lcs_fitness(s1, s2):
    def matcher(*strings):
        return len(long_substr(*strings))
    return match_to_ratio(matcher, s1, s2, False)

def overlap_fitness(s1, s2):
    """Determine fitness by considering only letters in identical positions."""
    def matcher(a, b):
        common = 0
        for i in xrange(min(len(a), len(b))):
            common += 1 if a[i] == b[i] else 0
        return common
    return match_to_ratio(matcher, s1, s2, False)

def random_string(chars, length, rand = random):
    """Generates a random string of `length` characters from `chars`."""
    return ''.join([rand.choice(chars) for ignore in xrange(length)])

class WeaselSimulator:
    """A genetic simulator."""
    class DEFAULTS:
        target_phrase = 'METHINKS IT IS LIKE A WEASEL'
        seed = random.randrange(sys.maxint)
        characters = string.uppercase + ' '
        num_children = 100
        mutate_chance = 0.1
        fitness = ['overlap']
        rotate_chance = 0.1
        rotate_bound = 5
        sync_rotate = False

    fitness_functions = {'levenshtein': levenshtein_fitness,
                         'sequence': sequence_matcher_fitness,
                         'blocks': matching_blocks_fitness,
                         'lcs': lcs_fitness,
                         'overlap': overlap_fitness}

    def __init__(self,
                 target_phrase = DEFAULTS.target_phrase,
                 seed = DEFAULTS.seed,
                 characters = DEFAULTS.characters,
                 num_children = DEFAULTS.num_children,
                 mutate_chance = DEFAULTS.mutate_chance,
                 initial_phrase = None,
                 fitness = DEFAULTS.fitness,
                 rotate_chance = DEFAULTS.rotate_chance,
                 rotate_bound = DEFAULTS.rotate_bound,
                 sync_rotate = DEFAULTS.sync_rotate):
        self.target_phrase = target_phrase
        self.phrase_length = len(self.target_phrase)
        self.rand = random.Random(seed)
        self.characters = characters
        self.num_children = num_children
        self.mutate_chance = mutate_chance
        if initial_phrase:
            self.initial_phrase = initial_phrase
        else:
            self.initial_phrase = random_string(self.characters, self.phrase_length, self.rand)
        self.fitness = [WeaselSimulator.fitness_functions.get(i) for i in fitness]
        self.fitness_names = fitness
        self.rotate_chance = rotate_chance
        self.rotate_bound = rotate_bound
        self.sync_rotate = sync_rotate

        self.generation = 0
        self.candidates = []
        self.best_candidate = self.initial_phrase
        self.current_fitness = self.calc_fitness(self.target_phrase, self.best_candidate)

    def print_initial(self):
        """Show some initial information."""
        print("Target: '%s'" % self.target_phrase)
        print("Fitness Functions: %r" % self.fitness_names)
        print("Initial phrase: '%s'" % self.initial_phrase)
        print("Initial fitness: %f" % self.calc_fitness(self.target_phrase, self.best_candidate))
        print("Characters: '%s'" % self.characters)
        print("Number of Children: %d" % self.num_children)
        print("Mutation Chance: %f" % self.mutate_chance)
        print("------\n")

    def print_generation(self):
        print("Generation: %d" % self.generation)
        print("Best Child: '%s'" % self.best_candidate)
        print("Current Fitness: %f" % self.current_fitness)
        print("------\n")

    def calc_fitness(self, target, candidate):
        return sum([func(target, candidate) for func in self.fitness]) / len(self.fitness)

    def flip(self, p):
        return self.rand.random() < p

    def mutate_letter_maybe(self, letter):
        """Return a (possibly) mutated version of letter.

        self.mutate_chance determines how likely it is for the letter to
        mutate."""
        return self.rand.choice(self.characters) if (self.flip(self.mutate_chance)) else letter

    def rotate_maybe(self, source):
        if self.flip(self.rotate_chance):
            return self.rotate(source)
        else:
            return source

    def rotate(self, source):
        bound = min(self.rotate_bound, self.rand.randrange(self.phrase_length))
        amount = self.rand.randint(-bound, bound)
        d = collections.deque(source)
        d.rotate(amount)
        res = ''.join(d)
        return res

    def mutate_copy(self, source):
        if not self.sync_rotate:
            source = self.rotate_maybe(source)
        return ''.join(map(self.mutate_letter_maybe, source))

    def children(self, parent):
        if self.sync_rotate:
            parent = self.rotate_maybe(parent)
        for i in xrange(self.num_children):
            yield self.mutate_copy(parent)

    def generations(self):
        while self.best_candidate != self.target_phrase:
            parent = self.best_candidate
            children = self.children(parent)
            self.generation += 1
            first_child = children.next()
            candidate = (first_child, self.calc_fitness(self.target_phrase, first_child))
            for child in children:
                dist = self.calc_fitness(self.target_phrase, child)
                if dist > candidate[1]:
                    candidate = (child, dist)
            print "Generation best fitness: %f" % candidate[1]
            print "Generation best child: '%s'" % candidate[0]
            print "Distance from parent: %f" % self.calc_fitness(parent, candidate[0])
            if candidate[1] >= self.current_fitness:
                self.best_candidate, self.current_fitness = candidate

            self.print_generation()
            yield

def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(description='Simulate a weasel.')
    parser.add_argument('--seed', '-i', type=int, default=WeaselSimulator.DEFAULTS.seed,
                        help='Seed for the random number generator.')
    parser.add_argument('--characters', '-c', type=str, default=WeaselSimulator.DEFAULTS.characters,
                        help='Valid characters to try in candidates.')
    parser.add_argument('--children', '-n', type=int, default=WeaselSimulator.DEFAULTS.num_children,
                        help='Number of children per generation.', dest='num_children')
    parser.add_argument('--mutate', '-m', type=float, default=WeaselSimulator.DEFAULTS.mutate_chance,
                        help='Chance that any individual character will mutate. A float in [0.0, 1.0].',
                        dest='mutate_chance')
    parser.add_argument('--fitness', '-f', type=str, default=argparse.SUPPRESS,
                        help='The fitness functions to use.', choices=WeaselSimulator.fitness_functions,
                        dest='fitness', action='append')
    parser.add_argument('--rotate', '-r', type=float, default=WeaselSimulator.DEFAULTS.rotate_chance,
                        help='Chance that the string will be rotated. A float in [0.0, 1.0].',
                        dest='rotate_chance')
    parser.add_argument('--rotate-bound', '-b', type=int, default=WeaselSimulator.DEFAULTS.rotate_bound,
                        help='Maximum amount by which the string will be rotated.',
                        dest='rotate_bound')
    parser.add_argument('--sync-rotate', '-s', default=WeaselSimulator.DEFAULTS.sync_rotate,
                        help='If True, rotate the entire generation at once. (default: %(default)s)',
                        nargs='?', const=True, dest='sync_rotate')
    parser.add_argument('target_phrase', metavar='TARGET', type=str, default=WeaselSimulator.DEFAULTS.target_phrase,
                        help='Target string.', nargs='?')
    parser.add_argument('initial_phrase', metavar='INITIAL', type=str, default=None,
                        help='Initial candidate string.', nargs='?')
    args = parser.parse_args(argv[1:])

    # I don't think I'm supposed to use __dict__ directly, but it works here,
    # so...
    sim = WeaselSimulator(**args.__dict__)
    sim.print_initial()
    for ign in sim.generations():
        pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
