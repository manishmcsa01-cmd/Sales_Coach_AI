import networkx as nx

class KnowledgeGraphBuilder:
    """Constructs a domain Knowledge Graph linking Merchants, Outlets, DSPs, Areas, and Scores."""

    def build_from_entities(self, areas, merchants, outlets, scores, dsps, assignments) -> nx.DiGraph:
        G = nx.DiGraph()

        for a in areas:
            G.add_node(f"area:{a.id}", type="Area", name=a.area_name, region=a.region)

        for m in merchants:
            G.add_node(f"merchant:{m.id}", type="Merchant", name=m.business_name, risk_tier=m.risk_tier)

        for d in dsps:
            G.add_node(f"dsp:{d.id}", type="DSP", name=d.name, email=d.email, role=d.role)
            if d.area_id:
                G.add_edge(f"dsp:{d.id}", f"area:{d.area_id}", relation="MANAGES" if d.role == "manager" else "OPERATES_IN")

        for o in outlets:
            G.add_node(f"outlet:{o.id}", type="Outlet", name=o.outlet_name, status=o.status, city=o.city)
            if o.merchant_id:
                G.add_edge(f"merchant:{o.merchant_id}", f"outlet:{o.id}", relation="OWNS")
            if o.area_id:
                G.add_edge(f"outlet:{o.id}", f"area:{o.area_id}", relation="LOCATED_IN")

        for s in scores:
            G.add_node(f"score:{s.id}", type="Score", priority=s.priority_score, factors=s.contributing_factors)
            G.add_edge(f"outlet:{s.outlet_id}", f"score:{s.id}", relation="SCORED_BY")

        for asgn in assignments:
            G.add_edge(f"dsp:{asgn.dsp_id}", f"outlet:{asgn.outlet_id}", relation="ASSIGNED_TO")

        return G

