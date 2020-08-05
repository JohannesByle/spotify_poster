import os
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from requests.exceptions import ReadTimeout
import time
import config

path = os.path.dirname(__file__)
data_path = os.path.join(path, "cache")
if not os.path.exists(data_path):
    os.mkdir(data_path)
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
            time.sleep(5)
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
