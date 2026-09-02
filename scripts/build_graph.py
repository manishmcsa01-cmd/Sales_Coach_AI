import pickle
from knowledge_graph.builder import KnowledgeGraphBuilder

if __name__ == "__main__":
    print("Building knowledge graph...")
    builder = KnowledgeGraphBuilder()
    G = builder.build_graph(None)
    with open("knowledge_graph.pkl", "wb") as f:
        pickle.dump(G, f)
    print("Graph built and saved to knowledge_graph.pkl")
