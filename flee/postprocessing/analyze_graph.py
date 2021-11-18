import matplotlib.pyplot as plt
import networkx as nx


def print_graph(vertices, edges, print_dist: bool = False) -> None:
    """
    Summary

    Args:
        vertices (TYPE): Description
        edges (TYPE): Description
        print_dist (bool, optional): Description
    """
    for v in vertices:
        print("Vertex name: ", v)
        if not print_dist:
            for e in edges:
                if e[0] == v:
                    print("-> ", e[1])
        else:
            for e in edges:
                if e[0] == v:
                    print("-> ", e[1], e[2])


def print_graph_nx(vertices, edges, print_dist=False):
    """
    Summary

    Args:
        vertices (TYPE): Description
        edges (TYPE): Description
        print_dist (bool, optional): Description
    """

    G = nx.DiGraph()
    # labels = []

    for v in vertices:
        G.add_node(v)

    for _ in vertices:
        for e in edges:
            G.add_edge(e[0], e[1], weight=int(e[2]))
            # labels += [(e[0], e[1]), e[2]]

    print("Nodes of graph: ")
    print(G.nodes())
    print("Edges of graph: ")
    print(G.edges())

    nx.draw(G, with_labels=True, node_color="y")
    # nx.draw_networkx_edge_labels(G,labels)
    plt.savefig("simulation_graph.png")  # save as png
    plt.show()
