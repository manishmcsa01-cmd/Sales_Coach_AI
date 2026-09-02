import networkx as nx

def get_outlet_neighbors(graph: nx.Graph, outlet_id: str) -> dict:
    if not graph.has_node(outlet_id):
        return {}
    neighbors = list(graph.neighbors(outlet_id))
    return {"neighbors": neighbors}

def get_similar_outlets(graph: nx.Graph, outlet_id: str, top_k: int = 5) -> list:
    # Placeholder for similar outlets calculation
    return []

def get_dsp_portfolio_graph(graph: nx.Graph, dsp_id: str) -> nx.Graph:
    # Placeholder for subgraph extraction
    return nx.Graph()
