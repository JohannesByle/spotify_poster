from get_cached import load_streaming_data, get_song, song_data_path, cache_path
from tqdm import tqdm
import pandas as pd
import os

artist_data_path = os.path.join(cache_path, "artist_data.json")
custom_genre_rules = {"hip hop": "hip-hop"}


def apply_custom_rules(genre):
    for key, val in custom_genre_rules.items():
        genre = genre.replace(key, val)
    return genre


def generate_cache():
    streaming_data = load_streaming_data()
    streaming_data['msPlayed'] = streaming_data.groupby(['trackName', 'artistName'])['msPlayed'].transform('sum')
    streaming_data = streaming_data[['artistName', 'trackName', 'msPlayed']].drop_duplicates().reset_index(drop=True)
    for index, song in tqdm(streaming_data.iterrows(), total=len(streaming_data)):
        get_song(song["artistName"], song["trackName"], silent=True)


def get_artists_network():
    df = pd.read_json(song_data_path)
    artists_dict = {}
    for index, song in df.iterrows():
        for artist in song["artist_data"]:
            name, id_ = artist["name"], artist["id"]
            genres = set([apply_custom_rules(genre) for genre in artist["genres"]])
            edges = {a["id"] for a in song["artist_data"] if a["id"] != artist["id"]}
            weights = {edge: 1 for edge in edges}
            if artist["type"] != "artist" or not genres:
                continue
            if id_ in artists_dict:
                assert artists_dict[id_]["genres"] == genres and artists_dict[id_]["name"] == name
                artists_dict[id_]["duration_ms"] += song["duration_ms"]
                artists_dict[id_]["edges"] = artists_dict[id_]["edges"].union(edges)
                for edge in edges:
                    artists_dict[id_]["weights"][edge] = artists_dict[id_]["weights"].get(edge, 0) + 1
                continue
            artists_dict[id_] = {"genres": genres,
                                 "name": name,
                                 "edges": edges,
                                 "duration_ms": song["duration_ms"],
                                 "weights": weights}
    for id_ in artists_dict:
        artists_dict[id_]["edges"] = [n for n in artists_dict[id_]["edges"] if n in artists_dict]
    artists_dict = pd.DataFrame(artists_dict).transpose()
    artists_dict.to_json(artist_data_path)
    return artists_dict


def get_genre_terms(num_terms=5):
    df = pd.read_json(song_data_path)
    genres_dict = {}
    for index, song in df.iterrows():
        for artist in song["artist_data"]:
            for genre in artist["genres"]:
                genre = apply_custom_rules(genre)
                duration_ms = genres_dict.get(genre, {}).get("duration_ms", 0) + song["duration_ms"]
                genres_dict[genre] = {"duration_ms": duration_ms}
    genre_terms = {}
    for genre in genres_dict:
        for term in genre.split():
            genre_terms[term] = genre_terms.get(term, 0) + genres_dict[genre]["duration_ms"]
    genre_terms = dict(pd.Series(genre_terms).sort_values(ascending=False).iloc[:num_terms])
    return genre_terms
