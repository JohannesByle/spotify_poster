import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go
from matplotlib.cm import get_cmap
from colorutils import Color
import plotly.io as pio
import os
import kaleido
from generate_data import get_genre_terms, get_artists_network
import scipy
import numpy as np

path = os.path.dirname(__file__)
out_path = os.path.join(path, "graphs")
if not os.path.exists(out_path):
    os.mkdir(out_path)


def flatten_lists(data):
    nodes = []
    for n in data:
        nodes += n
    return set(nodes)


def generate_graph_dict(data):
    graph = {n: flatten_lists(data[data.apply(lambda x: n in x)]) for n in flatten_lists(data)}
    [graph[n].remove(n) for n in graph]
    return graph


def generate_graph_networkx(data, graph=None, iterations=100):
    if not graph:
        graph = generate_graph_dict(data)
    g = nx.Graph()
    for k, vs in graph.items():
        # g.add_edge(k, k)
        for v in vs["edges"]:
            if v in list(graph):
                g.add_edge(k, v, weight=vs["weights"][v])
    return g, nx.spring_layout(g, iterations=iterations)


def generate_plotly_graph(num_terms=5, num_points=100, cm="plasma", min_size=10, max_size=40, iterations=100,
                          artist=None):
    artist_id = None
    genre_terms = get_genre_terms(num_terms=num_terms)
    df = get_artists_network()
    if artist:
        num_points = len(df)
    df = df.sort_values("duration_ms", ascending=False).iloc[:num_points]
    if artist:
        artist_id = df[df["name"] == artist].index
        if len(artist_id) > 1:
            raise Exception("Non-unique artist name")
        artist_id = artist_id[0]
    df["edges"] = df["edges"].apply(lambda x: set([n for n in x if n in df.index]))
    df = df[df["edges"].apply(lambda x: len(x) != 0)]
    graph = {n: {"edges": df.loc[n, "edges"], "weights": df.loc[n, "weights"]} for n in df.index}
    g, pos = generate_graph_networkx(None, graph=graph, iterations=iterations)
    if artist_id:
        remove_nodes = [n for n in g.nodes if not nx.has_path(g, n, artist_id)]
        [g.remove_node(n) for n in remove_nodes]
        df = df.loc[list(g.nodes)]
    c_map = get_cmap(cm)

    def resize(n, data):
        return min_size + (max_size - min_size) * ((n - min(data)) / (max(data) - min(data)))

    df["size"] = resize(df["duration_ms"], df["duration_ms"])
    df[[f"{term}_size" for term in genre_terms]] = None
    current_size = df["size"].copy()
    for term in genre_terms:
        rows = df["genres"].apply(lambda x: any([term in genre.split() for genre in x]))
        df.loc[rows, f"{term}_size"] = current_size
        df.loc[~rows, f"{term}_size"] = np.nan
        current_size.loc[rows] *= 0.6

    def add_scatter(df_, label, color, add_text=True, alpha=1.0):
        node_x = []
        node_y = []
        for node in df_.index:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            name=label,
            marker=dict(
                color=f"rgba({','.join([str(round(n, 5)) for n in color[:3]] + [str(alpha)])})",
                size=10,
                line_width=2),
            showlegend=True)
        if add_text:
            node_trace.text = list(df_["name"] + ": {" + df_["genres"].apply(lambda x_: ", ".join(x_)) + "}")
        node_trace.marker.size = list(df_["size"])
        node_trace.marker.line.width = 0
        return node_trace

    node_scatter = []
    for n, term in enumerate(genre_terms):
        sub_df = df.copy()
        sub_df = sub_df[~pd.isna(sub_df[f"{term}_size"])]
        sub_df["size"] = sub_df[f"{term}_size"]
        node_scatter += [add_scatter(sub_df, label=term, color=c_map(n / len(genre_terms)), add_text=False)]
    df["size"] = df["size"]
    rows = pd.notna(df[[f"{term}_size" for term in genre_terms]]).sum(axis=1).astype(bool)
    node_scatter += [add_scatter(df[~rows], label="Other", color=(0, 0, 0), alpha=1)]
    node_scatter += [add_scatter(df[rows], label="", color=(0, 0, 0), alpha=0.0)]
    edge_traces = []
    weights = set()
    df["weights"].apply(lambda x: [weights.add(v) for k, v in x.items()])
    for weight in weights:
        edge_x = []
        edge_y = []
        for edge in g.edges():
            if g.get_edge_data(edge[0], edge[1])["weight"] != weight:
                continue
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=round(weight ** 0.75, 5), color='#888'),
            hoverinfo="none",
            mode='lines',
            name=f"{weight} songs")
        edge_traces.append(edge_trace)
    fig = go.Figure(data=edge_traces + node_scatter,
                    layout=go.Layout(
                        showlegend=True,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    pio.write_image(fig, os.path.join(out_path, "network_graph.png"), width=int(1920 * 0.5), height=int(1080 * 0.5),
                    scale=5)
    pio.write_html(fig, os.path.join(out_path, "network_graph.html"))
    fig.show()
