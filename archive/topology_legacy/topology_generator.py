import networkx as nx
import numpy as np

"""
Refugee Topology Generator

Defines 8 fundamental topology types for systematic refugee movement analysis.
Each function accepts a `size_scale` parameter (roughly number of nodes)
and returns a NetworkX DiGraph with 'type' (conflict, town, camp), 'x', 'y',
'capacity', and 'conflict' attributes.
"""

def set_node_defaults(G):
    """Ensure all nodes have basic attributes if missing."""
    for n in G.nodes():
        if 'type' not in G.nodes[n]: G.nodes[n]['type'] = 'town'
        if 'capacity' not in G.nodes[n]: G.nodes[n]['capacity'] = 2000
        if 'conflict' not in G.nodes[n]: G.nodes[n]['conflict'] = 0.0
        if 'x' not in G.nodes[n]: G.nodes[n]['x'] = np.random.uniform(0, 200)
        if 'y' not in G.nodes[n]: G.nodes[n]['y'] = np.random.uniform(0, 200)
    for u, v in G.edges():
        if 'distance' not in G.edges[u,v]: G.edges[u,v]['distance'] = 20.0

def get_topology(name, size_scale=50):
    """Factory function to get topology by name."""
    generators = {
        "Linear": generate_linear,
        "Dendritic": generate_dendritic,
        "Lattice": generate_lattice,
        "HubAndSpoke": generate_hub_and_spoke,
        "Bottleneck": generate_bottleneck,
        "Parallel": generate_parallel,
        "SmallWorld": generate_small_world,
        "Random": generate_random
    }
    if name in generators:
        return generators[name](size_scale)
    else:
        raise ValueError(f"Unknown topology: {name}")

# 1. Linear (Corridor)
def generate_linear(N):
    G = nx.path_graph(N, create_using=nx.DiGraph)
    # Relabel to strings
    nx.relabel_nodes(G, {i: f"Loc_{i}" for i in range(N)}, copy=False)
    
    # Layout: Horizontal line
    for i in range(N):
        name = f"Loc_{i}"
        G.nodes[name]['x'] = i * (200 / N)
        G.nodes[name]['y'] = 100
        
        if i == 0:
            G.nodes[name]['type'] = 'conflict'
            G.nodes[name]['conflict'] = 1.0
            G.nodes[name]['capacity'] = -1
        elif i == N - 1:
            G.nodes[name]['type'] = 'camp'
            G.nodes[name]['conflict'] = 0.0
            G.nodes[name]['capacity'] = 50000
        else:
            G.nodes[name]['type'] = 'town'
            G.nodes[name]['conflict'] = max(0, 0.5 - i/N) # Decay

    set_node_defaults(G)
    return G

# 2. Dendritic (Hierarchical)
def generate_dendritic(N):
    # Balanced tree approximation
    branching = 3
    # N = (branching^(depth+1) - 1) / (branching - 1)
    # Solve for depth roughly
    depth = int(np.log(N * (branching - 1) + 1) / np.log(branching)) - 1
    depth = max(2, depth)
    
    G = nx.balanced_tree(branching, depth, create_using=nx.Graph).to_directed()
    # Relabel
    mapping = {i: f"Loc_{i}" for i in G.nodes()}
    nx.relabel_nodes(G, mapping, copy=False)
    
    # Root is Safe Zone (0)
    root = "Loc_0"
    G.nodes[root]['type'] = 'camp'
    G.nodes[root]['x'] = 200
    G.nodes[root]['y'] = 100
    G.nodes[root]['conflict'] = 0.0
    G.nodes[root]['capacity'] = 50000
    
    # Leaves are Conflict Zones
    leaves = [x for x in G.nodes() if G.out_degree(x) == 1 and G.in_degree(x) == 1] 
    # In balanced_tree directed, edges go parent->child usually or bidirectional?
    # nx.balanced_tree returns undirected. .to_directed() makes it bidirectional.
    # We want flow towards root.
    
    # Rebuild simple flow tree manually to ensure directionality
    G = nx.DiGraph()
    G.add_node("Root", type="camp", x=200, y=100, capacity=50000, conflict=0.0)
    
    current_layer = ["Root"]
    count = 1
    
    layer_width = 100
    
    for d in range(1, depth + 1):
        next_layer = []
        y_step = 200 / (len(current_layer) * branching + 1)
        y_pos = 0
        
        for parent in current_layer:
            for b in range(branching):
                name = f"Node_{count}"
                count += 1
                if count > N: break
                
                x = 200 - (d * (180/depth))
                y = y_pos + y_step
                y_pos += y_step
                
                is_leaf = (d == depth)
                l_type = 'conflict' if is_leaf else 'town'
                conf = 1.0 if is_leaf else 0.1
                
                G.add_node(name, type=l_type, x=x, y=y, conflict=conf, capacity=5000)
                G.add_edge(name, parent, distance=20.0)
                next_layer.append(name)
        current_layer = next_layer
        if count > N: break
        
    set_node_defaults(G)
    return G

# 3. Lattice (Grid)
def generate_lattice(N):
    side = int(np.sqrt(N))
    G = nx.grid_2d_graph(side, side)
    G = nx.DiGraph(G)
    mapping = {n: f"Loc_{n[0]}_{n[1]}" for n in G.nodes()}
    nx.relabel_nodes(G, mapping, copy=False)
    
    # Corner to Corner
    start = f"Loc_0_0"
    end = f"Loc_{side-1}_{side-1}"
    
    for n in G.nodes():
        parts = n.split('_')
        r, c = int(parts[1]), int(parts[2])
        G.nodes[n]['x'] = c * (200/side)
        G.nodes[n]['y'] = r * (200/side)
        G.nodes[n]['type'] = 'town'
        
        if n == start:
            G.nodes[n]['type'] = 'conflict'
            G.nodes[n]['conflict'] = 1.0
        elif n == end:
            G.nodes[n]['type'] = 'camp'
            G.nodes[n]['conflict'] = 0.0
            G.nodes[n]['capacity'] = 50000
    
    set_node_defaults(G)
    return G

# 4. Hub And Spoke (Star)
def generate_hub_and_spoke(N):
    G = nx.DiGraph()
    # Hub
    G.add_node("Hub", type="town", x=100, y=100, capacity=10000, conflict=0.2)
    
    # Safe Zone (connected to Hub)
    G.add_node("SafeZone", type="camp", x=180, y=100, capacity=50000, conflict=0.0)
    G.add_edge("Hub", "SafeZone", distance=50.0)
    
    num_spokes = N - 2
    for i in range(num_spokes):
        name = f"Spoke_{i}"
        angle = 2 * np.pi * i / num_spokes
        x = 100 + 80 * np.cos(angle)
        y = 100 + 80 * np.sin(angle)
        
        # Half conflict, half towns
        if i < num_spokes / 2:
            l_type = 'conflict'
            conf = 1.0
        else:
            l_type = 'town'
            conf = 0.1
            
        G.add_node(name, type=l_type, x=x, y=y, conflict=conf, capacity=2000)
        G.add_edge(name, "Hub", distance=40.0)
        
    set_node_defaults(G)
    return G

# 5. Bottleneck (Hourglass)
def generate_bottleneck(N):
    G = nx.DiGraph()
    # Bridge Node
    G.add_node("Bridge", type="town", x=100, y=100, capacity=2000, conflict=0.5)
    G.add_node("SafeZone", type="camp", x=180, y=100, capacity=50000, conflict=0.0)
    G.add_edge("Bridge", "SafeZone", distance=50.0)
    
    # Sources (Left)
    num_sources = (N - 2) // 2
    for i in range(num_sources):
        name = f"Source_{i}"
        G.add_node(name, type="conflict", x=20, y=20 + i*(160/num_sources), conflict=1.0, capacity=-1)
        G.add_edge(name, "Bridge", distance=80.0)
        
    # Transit/Distractors (Right, but dead ends or loops)
    # Actually, usually bottleneck implies many in -> one path -> out.
    # Let's just make it huge fan-in.
    
    set_node_defaults(G)
    return G

# 6. Parallel (Ladder)
def generate_parallel(N):
    # Multiple distinct paths from Source to Sink
    G = nx.DiGraph()
    G.add_node("Conflict", type="conflict", x=20, y=100, conflict=1.0)
    G.add_node("SafeZone", type="camp", x=180, y=100, conflict=0.0)
    
    num_paths = max(2, (N - 2) // 3)
    path_len = 3
    
    count = 0
    for p in range(num_paths):
        prev = "Conflict"
        y_offset = 100 + (p - num_paths/2) * 30
        
        for step in range(path_len):
            name = f"Path_{p}_Step_{step}"
            count += 1
            x = 20 + (step + 1) * (160 / (path_len + 1))
            G.add_node(name, type="town", x=x, y=y_offset, conflict=0.2)
            G.add_edge(prev, name, distance=20.0)
            prev = name
            
        G.add_edge(prev, "SafeZone", distance=20.0)
        
    set_node_defaults(G)
    return G

# 7. Small World (Watts-Strogatz variant)
def generate_small_world(N):
    # Ring lattice + shortcuts
    G = nx.watts_strogatz_graph(N, k=4, p=0.3).to_directed()
    # Mapping
    mapping = {i: f"Loc_{i}" for i in G.nodes()}
    nx.relabel_nodes(G, mapping, copy=False)
    
    # Circular layout
    for i in range(N):
        name = f"Loc_{i}"
        angle = 2 * np.pi * i / N
        G.nodes[name]['x'] = 100 + 80 * np.cos(angle)
        G.nodes[name]['y'] = 100 + 80 * np.sin(angle)
        G.nodes[name]['type'] = 'town'
        G.nodes[name]['conflict'] = 0.1
        
    # Pick source and sink opposite
    G.nodes["Loc_0"]['type'] = 'conflict'
    G.nodes["Loc_0"]['conflict'] = 1.0
    
    target = f"Loc_{N//2}"
    G.nodes[target]['type'] = 'camp'
    G.nodes[target]['conflict'] = 0.0
    G.nodes[target]['capacity'] = 50000
    
    # Ensure edges have distance
    for u,v in G.edges():
        # Euclidean distance
        x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
        x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
        dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
        G.edges[u,v]['distance'] = dist
        
    set_node_defaults(G)
    return G

# 8. Random (Erdos-Renyi) - Baseline chaos
def generate_random(N):
    G = nx.erdos_renyi_graph(N, p=0.15, directed=True)
    while not nx.is_weakly_connected(G):
        G = nx.erdos_renyi_graph(N, p=0.15, directed=True)
        
    mapping = {i: f"Loc_{i}" for i in G.nodes()}
    nx.relabel_nodes(G, mapping, copy=False)
    
    # Random layout
    pos = nx.spring_layout(G, scale=100, center=(100,100))
    for n, p in pos.items():
        G.nodes[n]['x'] = p[0]
        G.nodes[n]['y'] = p[1]
        G.nodes[n]['type'] = 'town'
        G.nodes[n]['conflict'] = np.random.uniform(0, 0.5)
        
    # Max degree node as Safe Zone? Or random?
    # Let's pick random source and sink
    nodes = list(G.nodes())
    src = nodes[0]
    dst = nodes[-1]
    
    G.nodes[src]['type'] = 'conflict'
    G.nodes[src]['conflict'] = 1.0
    
    G.nodes[dst]['type'] = 'camp'
    G.nodes[dst]['conflict'] = 0.0
    
    # Calc distances
    for u,v in G.edges():
        x1, y1 = G.nodes[u]['x'], G.nodes[u]['y']
        x2, y2 = G.nodes[v]['x'], G.nodes[v]['y']
        G.edges[u,v]['distance'] = np.sqrt((x2-x1)**2 + (y2-y1)**2)

    set_node_defaults(G)
    return G

