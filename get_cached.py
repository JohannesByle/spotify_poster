import os
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from requests.exceptions import ReadTimeout
import time
from config import special_rules
from urllib.request import urlretrieve
from tqdm import tqdm
import json
from urllib.parse import quote

path = os.path.dirname(__file__)
data_path = os.path.join(path, "cache")
if not os.path.exists(data_path):
    os.mkdir(data_path)
spotify_data_path = os.path.join(path, "MyData")
if not os.path.exists(spotify_data_path):
    raise Exception("Cannot find spotify data, make sure you are in a directory containing the spotify MyData folder")
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
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
        artist_data = []
        for n in song_data["artists"]:
            artist_data += [spotify.artist(n["id"])]
        song_data["artist_data"] = artist_data
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

    # Load spotify listening data from disk
    streaming_data = pd.DataFrame()
    for file in os.listdir(spotify_data_path):
        if file.startswith("StreamingHistory"):
            with open(os.path.join(spotify_data_path, file), "r", encoding="UTF") as f:
                streaming_data = streaming_data.append(pd.DataFrame(json.load(f)))
    streaming_data = streaming_data.reset_index(drop=True)

    streaming_data['msPlayed'] = streaming_data.groupby(['trackName', 'artistName'])['msPlayed'].transform('sum')
    streaming_data = streaming_data[['artistName', 'trackName', 'msPlayed']].drop_duplicates().reset_index(drop=True)
    streaming_data = streaming_data.sort_values(by="msPlayed", ascending=False)

    # Loop through most listened to songs to get most listened to albums
    album_data = pd.DataFrame(columns=["name", "file", "msPlayed", "artistData", "songData", "songs"])
    pbar = tqdm(total=album_count, desc="Getting albums")
    for index, row in streaming_data.iterrows():
        song = row["trackName"]
        artist = row["artistName"]

        if song in special_rules:
            song = special_rules[song]
        song_data = get_song(artist, song)

        if song_data is not None:
            album_name = song_data["album"]["name"]
            url = song_data["album"]["images"][0]["url"]
            file = url.split("/")[-1] + ".tiff"
            if not os.path.exists(os.path.join(path, "cache/album_art", file)):
                urlretrieve(url, os.path.join(path, "cache/album_art", file))
            if file not in list(album_data["file"]):

                album_data = album_data.append(pd.Series({"name": album_name, "file": file, "msPlayed": row["msPlayed"],
                                                          "artistData": song_data["artist_data"], "songData": song_data,
                                                          "songs": [song]}), ignore_index=True)
                pbar.update(n=1)
            else:
                index = album_data.index[album_data["file"] == file][0]
                album_data.loc[index, "msPlayed"] += row["msPlayed"]
                album_data.loc[index, "songs"] += [song]
        if len(album_data.index) >= album_count:
            break

    album_data = album_data.sort_values(by="msPlayed", ascending=False)
    return album_data
