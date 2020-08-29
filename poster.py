from PIL import Image
from tqdm import tqdm
import os
import matplotlib.pyplot as plt
from positions_functions import sequential, rand
import numpy as np
from get_cached import get_album_data
import random

path = os.path.dirname(__file__)


class Poster:

    def __init__(self):
        self.images = None
        self.positions = None
        self.album_data = None
        self.size = None
        self.album_sizes = None

    def roughly_proportional(self, num_sizes: int = 3, size_x: int = 6, size_y: int = 8) -> None:
        """

        :param num_sizes: the maximum number of times to divide the size of the albums
        :param size_x: the width of the poster in # of albums
        :param size_y: the height of the poster in # of albums
        :return: None
        """
        album_sizes = []
        new_poss = [[] for n in range(num_sizes)]
        counts = []
        count = 1
        if self.positions is None:
            poss = rand(sequential(size_x, size_y))
        else:
            poss = self.positions
        min_size = 640 * num_sizes
        for n in [poss[n::num_sizes] for n in range(num_sizes)]:
            counts += [count] * len(n)
            count += 1
        for n in range(len(poss)):
            min_size_i = int(min_size / counts[n])
            for x_i in range(counts[n]):
                for y_i in range(counts[n]):
                    x, y = poss[n]
                    new_poss[counts[n] - 1].append((x * min_size + x_i * min_size_i, y * min_size + y_i * min_size_i))
                    album_sizes.append((min_size_i, min_size_i))
        poss = []
        for temp in new_poss:
            if self.positions is None:
                random.shuffle(temp)
            poss += temp
        self.positions = poss
        self.album_sizes = album_sizes
        self.size = (size_x * min_size, size_y * min_size)

    def proportional(self, min_size: int = 32, album_count: int = 100) -> None:
        """

        :param min_size: the smallest size for an album in pixels
        :param album_count: the number of albums to include in the poster
        :return: None
        """
        from rpack import pack, enclosing_size
        if self.album_data is None or len(self.album_data.index) < album_count:
            album_data = get_album_data(album_count)
        else:
            album_data = self.album_data
        album_sizes = np.log(np.array(album_data["msPlayed"]))
        album_sizes = (album_sizes / min(album_sizes)) * min_size
        album_sizes = [(int(n), int(n)) for n in album_sizes]
        new_poss = pack(album_sizes)
        self.album_data = album_data
        self.positions = new_poss
        self.album_sizes = album_sizes
        self.size = enclosing_size(album_sizes, new_poss)

    def equal(self, size_x: int = 9, size_y: int = 16) -> None:
        """

        :param size_x: the width of the poster in # of albums
        :param size_y: the height of the poster in # of albums
        :return: None
        """
        min_size = 640
        if self.positions is None:
            poss = sequential(size_x, size_y)
        else:
            poss = self.positions
        album_sizes = [(min_size, min_size)] * len(poss)
        new_poss = [(poss[n][0] * album_sizes[n][0], poss[n][1] * album_sizes[n][1]) for n in range(len(poss))]
        self.positions = new_poss
        self.album_sizes = album_sizes
        self.size = (size_x * min_size, size_y * min_size)

    def colormap(self, colormap: str = "viridis", opacity: int = 175) -> None:
        """

        :param colormap: the colormap from the list of matplotlib colormaps
        :param opacity: the opacity of the colormap 255 is the darkest, 0 is the lightest
        :return: None
        """
        from matplotlib.cm import get_cmap
        if self.images is None:
            self.load_images()
        album_counts = np.array([np.log(n) for n in self.album_data["msPlayed"].values])
        cm = get_cmap(colormap)
        colors = (album_counts - min(album_counts)) / (max(album_counts) - min(album_counts))
        for n in range(len(self.images)):
            color = cm(colors[n])
            color = [int(255 * n) for n in color]
            color[3] = opacity
            color = tuple(color)
            self.images[n] = self.images[n].convert("RGBA")
            single_color = Image.new("RGBA", self.images[n].size, color)
            self.images[n].paste(single_color, (0, 0), single_color)

    def load_images(self):
        if self.album_data is None:
            if self.positions is None:
                raise Exception("album_data not yet loaded")
            self.album_data = get_album_data(len(self.positions))
        self.images = []
        for n in range(len(self.positions)):
            file = self.album_data.iloc[n, list(self.album_data.columns).index("file")]
            image = Image.open(os.path.join(path, "cache/album_art", file))
            if self.album_sizes is not None:
                if self.album_sizes[n] != image.size:
                    image = image.resize(self.album_sizes[n])
            if image.size != self.album_sizes[n]:
                image = image.resize(self.album_sizes[n])
            self.images.append(image)

    def create_poster(self, filename="poster"):
        if self.positions is None:
            self.positions = sequential()
        if self.album_data is None:
            self.album_data = get_album_data(len(self.positions))
        if self.images is None:
            self.load_images()
        new_image = Image.new(mode="RGB", size=self.size)
        for n in range(len(self.images)):
            new_image.paste(self.images[n], self.positions[n])
        filename = filename.split(".")[0]
        poster_path = os.path.join(os.path.dirname(__file__), "posters")
        if not os.path.exists(poster_path):
            os.mkdir(poster_path)
        file_saved = False
        n = 0
        new_filename = filename
        while not file_saved:
            new_filename = os.path.join(poster_path, new_filename)
            if not os.path.exists(new_filename + ".png"):
                new_image.save(new_filename + ".png")
                file_saved = True
            else:
                n += 1
                new_filename = filename + "-" + str(n)
