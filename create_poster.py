import pandas as pd
import json
import pickle
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from get_cached import get_artist, get_song
from tqdm import tqdm
from urllib.request import urlretrieve
from PIL import Image
import numpy as np
from config import special_rules, genre_tags, manual_includes
import random
from rpack import pack, enclosing_size
from matplotlib.cm import get_cmap

path = os.path.dirname(__file__)
data_path = os.path.join(path, "MyData")
if not os.path.exists(data_path):
    raise Exception("Cannot find spotify data, make sure you are in a directory containing the spotify MyData folder")
poster_path = os.path.join(path, "posters")
if not os.path.exists(os.path.join(path, "posters")):
    os.mkdir(os.path.join(path, "posters"))
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())


def get_album_data(album_count):
    if not os.path.exists(os.path.join(path, "cache/album_art")):
        os.mkdir(os.path.join(path, "cache/album_art"))
    if not os.path.exists(os.path.join(path, "cache/album_list_cache")):
        os.mkdir(os.path.join(path, "cache/album_list_cache"))
    cache_file = os.path.join(path, "cache/album_list_cache", "album_art-{}-{}.p".format(str(genre_tags), album_count))
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            album_counts, album_names, album_files = pickle.load(f)
        return album_counts, album_names, album_files

    # Load spotify listening data from disk
    streaming_data = pd.DataFrame()
    for file in os.listdir(data_path):
        if file.startswith("StreamingHistory"):
            with open(os.path.join(data_path, file), "r") as f:
                streaming_data = streaming_data.append(pd.DataFrame(json.load(f)))
    streaming_data = streaming_data.reset_index(drop=True)

    # Loop through most listened to songs to get most listened to albums
    album_files = []
    album_counts = []
    album_names = []
    value_counts = streaming_data["trackName"].value_counts()
    for song in value_counts.index:
        artist = streaming_data[streaming_data["trackName"] == song].reset_index().loc[0, "artistName"]
        artist_data = get_artist(artist)

        # If artist is manually specified to be included
        if manual_includes is None or artist not in manual_includes:
            # If genre_tags are specified filter by genre_tags
            if genre_tags is not None and not [n for n in genre_tags if n in str(artist_data["genres"])]:
                continue
        if song in special_rules:
            song = special_rules[song]
        song_data = get_song(artist, song)
        if song_data is not None:
            album_name = song_data["album"]["name"]
            url = song_data["album"]["images"][0]["url"]
            file = url.split("/")[-1] + ".jpg"
            if not os.path.exists(os.path.join(path, "cache/album_art", file)):
                urlretrieve(url, os.path.join(path, "cache/album_art", file))
            if album_name not in album_names:
                album_names.append(album_name)
                album_files.append(file)
                album_counts.append(value_counts[song])
            else:
                album_counts[album_names.index(album_name)] += value_counts[song]
        if len(album_names) >= album_count:
            break

    album_counts, album_names, album_files = zip(*reversed(sorted(zip(album_counts, album_names, album_files))))
    with open(cache_file, "wb") as f:
        pickle.dump((album_counts, album_names, album_files), f)
    return album_counts, album_names, album_files


def create_random_poster(size_x=6, size_y=8, sizes=3):
    # Create list of coordinates and shuffle their order
    poss = []
    [[poss.append((x, y)) for x in range(size_x)] for y in range(size_y)]
    random.shuffle(poss)

    # Create list of sizes
    counts = []
    count = 1
    album_count = 0
    for n in [poss[n::sizes] for n in range(sizes)]:
        counts += [count] * len(n)
        album_count += len(n) * (count ** 2)
        count += 1
    images = []
    album_counts, album_names, album_files = get_album_data(album_count)
    for album in album_files:
        images.append(Image.open(os.path.join(path, "cache/album_art", album)))

    # Resize images to preserve quality
    min_size = images[0].size[0] * sizes
    for n in range(len(images)):
        images[n] = images[n].resize((min_size, min_size))
    new_image = Image.new(mode=images[0].mode, size=(min_size * size_x, min_size * size_y))

    # Add images together
    n = 0
    i = 0
    for x, y in poss:
        count = counts[i]
        i += 1
        min_size_i = int(min_size / count)
        for x_i in range(count):
            for y_i in range(count):
                if n >= len(images):
                    break
                image = images[n].resize((min_size_i, min_size_i))
                new_image.paste(image, (x * min_size + x_i * min_size_i, y * min_size + y_i * min_size_i))
                n += 1

    # Save new image
    files = 0
    for file in os.listdir(poster_path):
        if file.startswith("random_poster-{}".format(str(genre_tags))):
            files += 1
    new_image.save(os.path.join(poster_path, "random_poster-{}-{}.png".format(str(genre_tags), files + 1)))


def create_true_size_poster(album_count=200, min_size=40):
    album_counts, album_names, album_files = get_album_data(album_count)
    album_counts = list((np.array(album_counts) / min(album_counts)) * min_size)
    album_counts = [int(n) for n in album_counts]
    images = []
    sizes = []
    for album in album_files:
        n = album_files.index(album)
        image = Image.open(os.path.join(path, "cache/album_art", album))
        image = image.resize((album_counts[n], album_counts[n]))
        images.append(image)
        sizes.append(image.size)
    packed = pack(sizes)
    new_image = Image.new(mode=images[0].mode, size=enclosing_size(sizes, packed))
    for image in images:
        new_image.paste(image, packed[images.index(image)])
    # Save new image
    files = 0
    for file in os.listdir(poster_path):
        if file.startswith("true_size_poster-{}".format(str(genre_tags))):
            files += 1
    new_image.save(os.path.join(poster_path, "true_size_poster-{}-{}.png".format(str(genre_tags), files + 1)))


def create_colormap_poster(size_x=9, size_y=16, colormap="viridis", opacity=150, order="radius"):
    # Create list of positions and sort them by radius
    poss = []
    [[poss.append((x, y)) for x in range(size_x)] for y in range(size_y)]

    if order == "radius":
        _, poss = zip(*sorted(zip([np.sqrt(n[0] ** 2 + n[1] ** 2) for n in poss], poss)))
    elif order == "random":
        random.shuffle(poss)

    # Create list of colors based on number of plays
    album_counts, album_names, album_files = get_album_data(size_x * size_y)
    album_counts = np.array(album_counts)
    colors = (album_counts - min(album_counts)) / (max(album_counts) - min(album_counts))
    cm = get_cmap(colormap)

    # Import images
    images = []
    for album in album_files:
        images.append(Image.open(os.path.join(path, "cache/album_art", album)))
    min_size = images[0].size[0]

    # Create new image
    new_image = Image.new(mode=images[0].mode, size=(min_size * size_x, min_size * size_y))
    n = 0
    for x, y in poss:
        new_image.paste(images[n], (x * min_size, y * min_size))
        color = cm(colors[n])
        color = [int(255 * n) for n in color]
        color[3] = opacity
        color = tuple(color)
        single_color = Image.new("RGBA", (min_size, min_size), color)
        new_image.paste(single_color, (x * min_size, y * min_size), single_color)
        n += 1
    # Save new image
    files = 0
    for file in os.listdir(poster_path):
        if file.startswith("colormap_poster-{}".format(str(genre_tags))):
            files += 1
    new_image = new_image.resize((int(new_image.size[0] / 2), int(new_image.size[1] / 2)))
    new_image.save(os.path.join(poster_path, "colormap_poster-{}-{}.png".format(str(genre_tags), files + 1)))


def create_color_sorted_poster(size_x=9, size_y=16):
    # Create list of positions and sort them by radius
    poss = []
    [[poss.append((x, y)) for x in range(size_x)] for y in range(size_y)]
    _, poss = zip(*sorted(zip([np.sqrt(n[0] ** 2 + n[1] ** 2) for n in poss], poss)))
    # Create list of colors based on number of plays
    album_counts, album_names, album_files = get_album_data(size_x * size_y)

    # Import images
    images = []
    colors = []
    for album in album_files:
        image = Image.open(os.path.join(path, "cache/album_art", album))
        images.append(image)
        array = np.array(image)
        colors.append(np.average(array))
    colors, images = zip(*sorted(zip(colors, images)))
    min_size = images[0].size[0]

    # Create new image
    new_image = Image.new(mode=images[0].mode, size=(min_size * size_x, min_size * size_y))
    n = 0
    for x, y in poss:
        new_image.paste(images[n], (x * min_size, y * min_size))
        n += 1

    # Save new image
    files = 0
    for file in os.listdir(poster_path):
        if file.startswith("color_sorted_poster-{}".format(str(genre_tags))):
            files += 1
    new_image = new_image.resize((int(new_image.size[0] / 2), int(new_image.size[1] / 2)))
    new_image.save(os.path.join(poster_path, "color_sorted_poster-{}-{}.png".format(str(genre_tags), files + 1)))
