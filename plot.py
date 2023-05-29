import networkx as nx
import plotly.graph_objects as go
import json


# Create a larger example graph
G = nx.random_geometric_graph(300, 0.2, dim=3,p=0.9)

# Generate the layout positions for the nodes
# pos = nx.spring_layout(G, dim=3)
# pos = nx.spring_layout(G,dim=3)
pos = nx.kamada_kawai_layout(G,dim=3)

# Create trace for nodes
node_trace = go.Scatter3d(
    x=[pos[node][0] for node in G.nodes()],
    y=[pos[node][1] for node in G.nodes()],
    z=[pos[node][2] for node in G.nodes()],
    mode="markers",
    marker=dict(size=5, color="blue"),
    text=list(G.nodes()),
)

# Create trace for edges
edge_trace = go.Scatter3d(
    x=[pos[src][0] for src, dest in G.edges()],
    y=[pos[src][1] for src, dest in G.edges()],
    z=[pos[src][2] for src, dest in G.edges()],
    mode="lines",
    line=dict(width=1, color="gray"),
)

# Create the figure
fig = go.Figure(data=[edge_trace, node_trace],
               layout=go.Layout(showlegend=False))


# Convert NetworkX graph to a JSON-compatible format
graph_data = nx.node_link_data(G)

# Save the graph data to a JSON file
with open('graph_data.json', 'w') as f:
    json.dump(graph_data, f)

# Set axis range and aspect ratio
fig.update_layout(scene=dict(
    xaxis=dict(range=[-1.2, 1.2]),
    yaxis=dict(range=[-1.2, 1.2]),
    zaxis=dict(range=[-1.2, 1.2]),
    aspectratio=dict(x=1, y=1, z=1),
    camera=dict(
        up=dict(x=0, y=0, z=1),
        eye=dict(x=0.1, y=-1.7, z=0.7)
    )
))

# Show the plot
fig.show()
