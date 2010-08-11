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
    target_phrase = 'METHINKS IT IS LIKE A WEASEL'
    seed = random.random()
    characters = string.uppercase + ' '
    num_children = 100
    mutate_chance = 0.05

    def __init__(self,
                 target_phrase = target_phrase,
                 seed = seed,
                 characters = characters,
                 num_children = num_children,
                 mutate_chance = mutate_chance,
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
        self.fitness = 0.0
        self.candidates = []
        self.best_candidate = self.initial_phrase

    def print_initial(self):
        """Show some initial information."""
        print("Target: %s" % self.target_phrase)
        print("Generation: %d" % self.generation)
        print("Characters: %s" % self.characters)
        print("Number of Children: %d" % self.num_children)
        print("Mutation Chance: %d" % self.mutate_chance)
        print("------\n")

    def print_generation(self):
        print("Generation: %d" % self.generation)
        print("Best Child: '%s'" % self.best_candidate)
        print("Current Fitness: %d" % self.fitness)
        print("------\n")

def make_children(parent):
    return [mutate_copy(parent) for i in xrange(num_children)]

def mutate_letter_maybe(letter):
    return random.choice(characters) if (flip(mutate_chance)) else letter

def mutate_copy(source):
    return ''.join(map(mutate_letter_maybe, source))

def flip(p):
    return random.random() < p

def run_generation():
    global best_child, best_distance, generation
    parent = best_child
    children = make_children(parent)
    generation += 1
    new_parent = children[0]
    child_dist = levenshtein(target_phrase, best_child)
    parent_dist = -1
    for child in children:
        dist = levenshtein(target_phrase, child)
        if dist < child_dist:
            child_dist = dist
            new_parent = child
            parent_dist = levenshtein(parent, child)
    print "Generation best dist: %d" % child_dist
    print "Generation best child: '%s'" % child
    print "Distance from parent: %d" % parent_dist
    if child_dist <= best_distance:
        best_distance = child_dist
        best_child = new_parent

    print_generation()

def init():
    global best_child, best_distance
    best_child = ''.join([random.choice(characters) for i in xrange(len(target_phrase))])
    best_distance = levenshtein(target_phrase, best_child)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    init()
    print_initial()
    while best_distance > 0:
        run_generation()

if __name__ == "__main__":
    sys.exit(main())
