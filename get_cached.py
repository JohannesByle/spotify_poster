import os
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from requests.exceptions import ReadTimeout
import time
from config import manual_includes, special_rules, genre_tags
from urllib.request import urlretrieve
from tqdm import tqdm
import json

path = os.path.dirname(__file__)
data_path = os.path.join(path, "cache")
if not os.path.exists(data_path):
    os.mkdir(data_path)
spotify_data_path = os.path.join(path, "MyData")
if not os.path.exists(spotify_data_path):
    raise Exception("Cannot find spotify data, make sure you are in a directory containing the spotify MyData folder")
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
if not os.path.exists(data_path + "/artist_data.json"):
    pd.DataFrame().to_json(data_path + "/artist_data.json")
artists = pd.read_json(data_path + "/artist_data.json")
if not os.path.exists(data_path + "/song_data.json"):
    pd.DataFrame().to_json(data_path + "/song_data.json")
songs = pd.read_json(data_path + "/song_data.json")


def spotify_search(query, query_type):
    while True:
        try:
            data = spotify.search(query, type=query_type)[query_type + "s"]["items"][0]
            return data
        except ReadTimeout:
            time.sleep(1)
            continue
        except IndexError:
            print("No results found: " + query)
            return None


def get_artist(artist):
    global artists

    def artist_search():
        global artists
        artists = artists.append(pd.Series(spotify_search("artist: {}".format(artist), "artist"), name=artist))
        artists.to_json(data_path + "/artist_data.json")

    if artist not in artists.index:
        artist_search()
    return artists.loc[artist]


def get_song(artist, song):
    global songs
    possible_songs = pd.DataFrame()
    if not songs.empty:
        possible_songs = songs[songs["name"] == song]
        for index, data in possible_songs.iterrows():
            if not [n for n in data["artists"] if n["name"] == artist]:
                possible_songs.drop(index)

    def album_search():
        global songs
        track = spotify_search("artist:{} track:{}".format(artist, song), "track")
        if track is None:
            return track
        song_data = pd.Series(track, name=track["id"])
        songs = songs.append(song_data)
        songs = songs.loc[~songs.index.duplicated(keep='first')]
        songs.to_json(data_path + "/song_data.json")
        return pd.DataFrame(song_data).iloc[0]

    if possible_songs.empty:
        possible_songs = album_search()
    if isinstance(possible_songs, pd.DataFrame):
        return possible_songs.iloc[0]
    else:
        return None


def get_album_data(album_count):
    # Make sure save locations exist
    if not os.path.exists(os.path.join(path, "cache/album_art")):
        os.mkdir(os.path.join(path, "cache/album_art"))

    # Load list of songs that have failed so that they are not checked twice
    if os.path.exists(os.path.join(data_path, "failed_songs.json")):
        with open(os.path.join(data_path, "failed_songs.json"), "r") as f:
            failed_songs = json.load(f)
    else:
        failed_songs = []

    # Load spotify listening data from disk
    streaming_data = pd.DataFrame()
    for file in os.listdir(spotify_data_path):
        if file.startswith("StreamingHistory"):
            with open(os.path.join(spotify_data_path, file), "r") as f:
                streaming_data = streaming_data.append(pd.DataFrame(json.load(f)))
    streaming_data = streaming_data.reset_index(drop=True)

    # Loop through most listened to songs to get most listened to albums
    album_data = pd.DataFrame(columns=["name", "file", "count"])
    value_counts = streaming_data["trackName"].value_counts()
    pbar = tqdm(total=album_count, desc="Getting albums")
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
        if song in failed_songs:
            continue
        song_data = get_song(artist, song)
        if song_data is not None:
            album_name = song_data["album"]["name"]
            url = song_data["album"]["images"][0]["url"]
            file = url.split("/")[-1] + ".png"
            if not os.path.exists(os.path.join(path, "cache/album_art", file)):
                urlretrieve(url, os.path.join(path, "cache/album_art", file))
            if album_name not in list(album_data["name"]):
                album_data = album_data.append({"name": album_name, "file": file, "count": value_counts[song]},
                                               ignore_index=True)
                pbar.update(n=1)
            else:
                album_data.loc[album_data["name"] == album_name, "count"] += value_counts[song]
        else:
            failed_songs += [song]
            with open(os.path.join(data_path, "failed_songs.json"), "w") as f:
                json.dump(failed_songs, f)
        if len(album_data.index) >= album_count:
            break

    album_data = album_data.sort_values(by="count", ascending=False)
    return album_data
