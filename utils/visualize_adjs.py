import json
import netgraph
import networkx as nx
import matplotlib.pyplot as plt

with open('../ips_adj.json') as f:
    d = json.load(f)


nodes = d['Nodes']
adjacents = d['Adjacents']

assert sorted(nodes.keys()) == sorted(adjacents.keys())

graph = nx.DiGraph(adjacents)



node_labels = {k:k for k in adjacents.keys()}

colors = {
    'S': 'blue',
    'N': 'green',
    'C': 'red'
}

node_color = {k: colors[k[0]] for k in adjacents.keys()}



netgraph.InteractiveGraph(graph, node_labels=node_labels, node_color=node_color, node_size=5, arrows=True, edge_width=3)

plt.title('Adjacents')
plt.show()
