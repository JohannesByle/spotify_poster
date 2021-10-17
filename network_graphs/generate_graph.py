import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go
from matplotlib.cm import get_cmap
from colorutils import Color
import plotly.io as pio
import os
from get_cached import path
import kaleido


def flatten_lists(data):
    nodes = []
    for n in data:
        nodes += n
    return set(nodes)


def generate_graph_dict(data):
    graph = {n: flatten_lists(data[data.apply(lambda x: n in x)]) for n in flatten_lists(data)}
    [graph[n].remove(n) for n in graph]
    return graph


def generate_graph_networkx(data, graph=None):
    if not graph:
        graph = generate_graph_dict(data)
    g = nx.Graph()
    for k, vs in graph.items():
        g.add_edge(k, k)
        for v in vs:
            if v in list(graph):
                g.add_edge(k, v)
    return g, nx.spring_layout(g)


def plotly_graph_pandas(df, cm="hsv"):
    graph = {df.loc[n, "node"]: df.loc[n, "edges"] for n in df["node"]}
    g, pos = generate_graph_networkx(None, graph=graph)

    cmap = get_cmap(cm)
    categories = list(flatten_lists(df["category"]))

    def get_color(cats):
        color = Color()
        for cat in cats:
            if not cat:
                new_color = cmap(0.5)
            else:
                new_color = cmap(categories.index(cat) / len(categories))[:3]
            color += Color([n * 255 for n in new_color])
        return "rgb({})".format(",".join([str(round(n / 255, 5)) for n in color]))

    df["color"] = df["category"].apply(lambda x: get_color(x))

    def add_scatter(sub_df, cat, min_size=10, max_size=30):

        def resize(n, data):
            return min_size + (max_size - min_size) * ((n - min(data)) / (max(data) - min(data)))

        node_x = []
        node_y = []
        for node in sub_df["node"]:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            name=cat,
            marker=dict(
                color=sub_df.iloc[0]["color"],
                size=10,
                line_width=2),
            showlegend=True)
        node_trace.text = list(sub_df["node"])
        num_connections = sub_df["edges"].apply(lambda x: len(x))
        node_trace.marker.size = [resize(n, df["edges"].apply(lambda x: len(x))) for n in num_connections]
        return node_trace

    node_scatter = []
    n = 0
    for cat in pd.unique(df["category"].astype(str)):
        n += len(df[df["category"].astype(str) == cat].index)
        node_scatter += [add_scatter(df[df["category"].astype(str) == cat], cat)]

    edge_x = []
    edge_y = []
    for edge in g.edges():
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
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')
    fig = go.Figure(data=[edge_trace] + node_scatter,
                    layout=go.Layout(
                        showlegend=True,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    pio.write_image(fig, os.path.join(path, "posters/network_graph.png"), width=int(1920 * 0.5), height=int(1080 * 0.5),
                    scale=5)
    fig.show()
