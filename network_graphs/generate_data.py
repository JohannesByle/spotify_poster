import pandas as pd
import json
from get_cached import data_path
import os
from generate_graph import generate_graph_dict
import spotipy
from spotipy import SpotifyClientCredentials
from tqdm import tqdm

categories = ["german", "rap", "turkish"]
artists_edges_path = os.path.join(data_path, "artists_edges.json")
artists_df_path = os.path.join(data_path, "artists_df.pickle")


def generate_artist_df():
    data = pd.read_json(os.path.join(data_path, "song_data.json"))
    data["artist_names"] = data["artist_data"].apply(lambda x: [n["name"] for n in x])
    data["artist_genres"] = data["artist_data"].apply(lambda x: {n["name"]: n["genres"] for n in x})
    data["artist_ids"] = data["artist_data"].apply(lambda x: {n["name"]: n["id"] for n in x})
    artists_graph = generate_graph_dict(data["artist_names"])
    artists = pd.DataFrame(index=artists_graph.keys())
    artists["node"] = artists.index
    artists["edges"] = artists_graph.values()
    artists["genres"] = None
    artists["category"] = None
    for index, row in data.iterrows():
        for artist in row["artist_genres"]:
            genres = row["artist_genres"][artist]
            artists.loc[artist, "genres"] = genres
            artists.loc[artist, "category"] = [i for i in categories if [n for n in genres if i in n]]
            artists.loc[artist, "id"] = row["artist_ids"][artist]
    print(artists)
    artists.to_pickle("artists_df.pickle")


def get_artists_edges():
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    artists = pd.read_pickle(artists_df_path)
    for index, row in tqdm(artists.iterrows(), total=len(artists.index)):
        with open(artists_edges_path, "r") as f:
            artists_edges = json.load(f)
        artist = row["node"]
        if artist in artists_edges:
            continue
        artists_edges[artist] = []
        albums = sp.artist_albums(row["id"])["items"]
        for album in albums:
            songs = sp.album(album["id"])["tracks"]["items"]
            for song in songs:
                artists_edges[artist] += [n["name"] for n in song["artists"] if
                                          n["name"] != artist and n["name"] in list(artists["node"])]
        artists_edges[artist] = list(set(artists_edges[artist]))
        with open(artists_edges_path, "w") as f:
            json.dump(artists_edges, f)
