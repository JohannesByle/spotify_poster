import random
import numpy as np


def sequential(size_x: int = 9, size_y: int = 16) -> list:
    """

    :param size_x: the width of the poster in # of albums
    :param size_y: the height of the poster in # of albums
    :return: a sorted list of tuple coordinates (x, y)
    """
    poss = []
    [[poss.append((x, y)) for x in range(size_x)] for y in range(size_y)]
    return poss


def rand(poss: list) -> list:
    """

    :param poss: list of tuple coordinates (x, y)
    :return: randomly shuffled list of tuple coordinates (x, y)
    """
    random.shuffle(poss)
    return poss


def radius(poss: list, center_point: tuple = None) -> list:
    """

    :param poss: list of tuple coordinates (x, y)
    :param center_point: the point from which the distance is measured
    :return: a list of tuple coordinates (x, y) sorted by distance from the center_point
    """
    size_x = max([n[0] for n in poss])
    size_y = max([n[0] for n in poss])
    if center_point is None:
        center_point = (size_x / 2 - 1, size_y / 2 - 1)
    poss = sequential(size_x, size_y)

    def f(x1, y1, x2, y2):
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    _, poss = zip(*sorted(zip([f(n[0], n[1], center_point[0], center_point[1]) for n in poss], poss)))
    return poss


def manhattan(poss: list, center_point: tuple = None) -> list:
    """

    :param poss: list of tuple coordinates (x, y)
    :param center_point: the point from which the distance is measured
    :return: a list of tuple coordinates (x, y) sorted by distance from the center_point
    """
    size_x = max([n[0] for n in poss])
    size_y = max([n[0] for n in poss])
    if center_point is None:
        center_point = (size_x / 2 - 1, size_y / 2 - 1)
    poss = sequential(size_x, size_y)

    def f(x1, y1, x2, y2):
        return np.sqrt(abs(x1 - x2) + abs(y1 - y2))

    _, poss = zip(*sorted(zip([f(n[0], n[1], center_point[0], center_point[1]) for n in poss], poss)))
    return poss
