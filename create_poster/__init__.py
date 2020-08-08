import pandas as pd
import json
import pickle
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from get_cached import get_album_data
from tqdm import tqdm
from urllib.request import urlretrieve
from PIL import Image
import numpy as np
from config import genre_tags
import random
from rpack import pack, enclosing_size
from matplotlib.cm import get_cmap
from colorsys import rgb_to_hsv, rgb_to_hls
from colorthief import ColorThief
from .positions_functions import *
from .sizes_functions import *
import inspect

path = os.path.dirname(os.path.dirname(__file__))
poster_path = os.path.join(path, "posters")
if not os.path.exists(os.path.join(path, "posters")):
    os.mkdir(os.path.join(path, "posters"))
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())


def create_poster(positions="random", sizes="roughly-proportional", colormap=None, opacity=200):
    def run_func_from_arg(name, val, module):
        names = [n[0] for n in inspect.getmembers(module) if callable(n[1])]
        functions = [n[1] for n in inspect.getmembers(module) if callable(n[1])]
        if val in names:
            return functions[names.index(val)]()
        else:
            raise Exception("{} must be one of {}, but you entered {}".format(name, names, val))

    # Determine how the albums will be positioned on the page by determining the order of the coordinates
    run_func_from_arg("positions", positions, positions_functions)

    # Determine the sizes of the albums
    poss_array, album_sizes, image_size = run_func_from_arg("sizes", sizes, sizes_functions)

    # Load images
    album_data = get_album_data(len(album_sizes))
    images = []
    for n in tqdm(range(len(album_data)), desc="Loading images"):
        file = album_data.iloc[n, list(album_data.columns).index("file")]
        image = Image.open(os.path.join(path, "cache/album_art", file))
        if image.size != album_sizes[n]:
            image = image.resize(album_sizes[n])
        images.append(image)

    # Load colormap
    album_counts = np.array([np.log(n) for n in album_data["count"].values])
    colors = (album_counts - min(album_counts)) / (max(album_counts) - min(album_counts))
    cm = get_cmap(colormap)

    # Create new image
    new_image = Image.new(mode="RGB", size=image_size)

    # Add images to new image
    for n in tqdm(range(len(poss_array)), desc="Pasting images"):
        new_image.paste(images[n], poss_array[n])
        if colormap is not None:
            color = cm(colors[n])
            color = [int(255 * n) for n in color]
            color[3] = opacity
            color = tuple(color)
            single_color = Image.new("RGBA", album_sizes[n], color)
            new_image.paste(single_color, poss_array[n], single_color)

    # Save new image
    print("Saving image")
    file_number = 0
    file_name = "{}_{}".format(sizes, positions)
    for file in os.listdir(poster_path):
        if file.startswith(file_name):
            file_number += 1
    new_image.save(os.path.join(poster_path, "{}-{}.png".format(file_name, file_number)))
