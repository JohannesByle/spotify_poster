import numpy as np


def roughly_proportional(num_sizes=3):
    from .positions_functions import poss
    size_x = max([n[0] for n in poss])
    size_y = max([n[1] for n in poss])
    album_sizes = []
    new_poss = []
    counts = []
    count = 1
    for n in [poss[n::num_sizes] for n in range(num_sizes)]:
        counts += [count] * len(n)
        count += 1
    min_size = 640 * num_sizes
    for n in range(len(poss)):
        min_size_i = int(min_size / counts[n])
        for x_i in range(counts[n]):
            for y_i in range(counts[n]):
                x, y = poss[n]
                new_poss.append((x * min_size + x_i * min_size_i, y * min_size + y_i * min_size_i))
                album_sizes.append((min_size_i, min_size_i))
    return new_poss, album_sizes, (size_x * min_size, size_y * min_size)


def proportional(min_size=32, album_count=100):
    from get_cached import get_album_data
    from rpack import pack, enclosing_size
    album_data = get_album_data(album_count)
    album_sizes = np.log(np.array(album_data["count"]))
    album_sizes = (album_sizes / min(album_sizes)) * min_size
    album_sizes = [(int(n), int(n)) for n in album_sizes]
    new_poss = pack(album_sizes)
    return new_poss, album_sizes, enclosing_size(album_sizes, new_poss)


def equal():
    from .positions_functions import poss
    size_x = max([n[0] for n in poss])
    size_y = max([n[1] for n in poss])
    min_size = 640
    album_sizes = [(min_size, min_size)] * len(poss)
    new_poss = [(poss[n][0] * album_sizes[n][0], poss[n][1] * album_sizes[n][1]) for n in range(len(poss))]
    return new_poss, album_sizes, (size_x * min_size, size_y * min_size)
