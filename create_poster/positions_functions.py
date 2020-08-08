import random
import numpy as np

poss = []
size_x = 10
size_y = 16


def sequential():
    global poss, size_x, size_y
    poss = []
    [[poss.append((x, y)) for x in range(size_x)] for y in range(size_y)]
    return poss


def rand():
    global poss, size_x, size_y
    poss = sequential()
    return random.shuffle(poss)


def radius(center_point=None):
    global poss, size_x, size_y
    if center_point is None:
        center_point = (size_x / 2 - 1, size_y / 2 - 1)
    poss = sequential()

    def f(x1, y1, x2, y2):
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    _, poss = zip(*sorted(zip([f(n[0], n[1], center_point[0], center_point[1]) for n in poss], poss)))
    return poss


def manhattan(center_point=None):
    global poss, size_x, size_y
    if center_point is None:
        center_point = (size_x / 2 - 1, size_y / 2 - 1)
    poss = sequential()

    def f(x1, y1, x2, y2):
        return np.sqrt(abs(x1 - x2) + abs(y1 - y2))

    _, poss = zip(*sorted(zip([f(n[0], n[1], center_point[0], center_point[1]) for n in poss], poss)))
    return poss
