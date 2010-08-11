#!/usr/bin/env python

from __future__ import division

import random
import string
import sys

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

def levenshtein_fitness(s1, s2):
    """Calculate fitness based on Levenshtein distance.
    Returns a float in the range [0.0, 1.0]."""
    return abs(levenshtein(s1, s2) / max(len(s1), len(s2)) - 1)

def random_string(chars, length, rand = random):
    """Generates a random string of `length` characters from `chars`."""
    return ''.join([rand.choice(chars) for ignore in xrange(length)])

class WeaselSimulator:
    """A genetic simulator."""
    class DEFAULTS:
        target_phrase = 'METHINKS IT IS LIKE A WEASEL'
        seed = random.random()
        characters = string.uppercase + ' '
        num_children = 100
        mutate_chance = 0.05

    def __init__(self,
                 target_phrase = DEFAULTS.target_phrase,
                 seed = DEFAULTS.seed,
                 characters = DEFAULTS.characters,
                 num_children = DEFAULTS.num_children,
                 mutate_chance = DEFAULTS.mutate_chance,
                 initial_phrase = None):
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
        self.generation = 0
        self.candidates = []
        self.best_candidate = self.initial_phrase
        self.fitness = levenshtein_fitness(self.target_phrase, self.best_candidate)

    def print_initial(self):
        """Show some initial information."""
        print("Target: %s" % self.target_phrase)
        print("Initial phrase: %s" % self.initial_phrase)
        print("Initial fitness: %f" % levenshtein_fitness(self.target_phrase, self.best_candidate))
        print("Characters: %s" % self.characters)
        print("Number of Children: %d" % self.num_children)
        print("Mutation Chance: %f" % self.mutate_chance)
        print("------\n")

    def print_generation(self):
        print("Generation: %d" % self.generation)
        print("Best Child: '%s'" % self.best_candidate)
        print("Current Fitness: %f" % self.fitness)
        print("------\n")

    def flip(self, p):
        return self.rand.random() < p

    def mutate_letter_maybe(self, letter):
        """Return a (possibly) mutated version of letter.

        self.mutate_chance determines how likely it is for the letter to
        mutate."""
        return self.rand.choice(self.characters) if (self.flip(self.mutate_chance)) else letter

    def mutate_copy(self, source):
        return ''.join(map(self.mutate_letter_maybe, source))

    def children(self, parent):
        for i in xrange(self.num_children):
            yield self.mutate_copy(parent)

    def generations(self):
        while self.fitness is not 1.0:
            parent = self.best_candidate
            children = self.children(parent)
            self.generation += 1
            first_child = children.next()
            candidate = (first_child, levenshtein_fitness(self.target_phrase, first_child))
            for child in children:
                dist = levenshtein_fitness(self.target_phrase, child)
                if dist > candidate[1]:
                    candidate = (child, dist)
            print "Generation best fitness: %f" % candidate[1]
            print "Generation best child: '%s'" % candidate[0]
            print "Distance from parent: %f" % levenshtein_fitness(parent, candidate[0])
            if candidate[1] >= self.fitness:
                self.best_candidate, self.fitness = candidate

            self.print_generation()
            yield

def main(argv=None):
    if argv is None:
        argv = sys.argv

    sim = WeaselSimulator()
    sim.print_initial()
    for ign in sim.generations():
        pass

if __name__ == "__main__":
    sys.exit(main())
