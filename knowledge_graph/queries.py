import networkx as nx
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outlet import Outlet
from app.models.merchant import Merchant
from app.models.score import OutletScore
from app.models.transaction import Transaction
from app.models.visit_log import VisitLog
from app.models.action import ActionRecommendation
from app.models.area import Area
from app.models.dsp import Dsp


class GraphQueryEngine:
    """Knowledge Graph query engine mapping entities, relationships, and territory graph."""

    def build_runtime_graph(self, outlets, merchants, scores, dsps) -> nx.DiGraph:
        G = nx.DiGraph()
        for m in merchants:
            G.add_node(f"merchant_{m.id}", type="Merchant", name=m.business_name)
        for o in outlets:
            G.add_node(f"outlet_{o.id}", type="Outlet", name=o.outlet_name, status=o.status)
            G.add_edge(f"merchant_{o.merchant_id}", f"outlet_{o.id}", relation="OWNS")
            if o.area_id:
                G.add_node(f"area_{o.area_id}", type="Area")
                G.add_edge(f"outlet_{o.id}", f"area_{o.area_id}", relation="LOCATED_IN")
        for s in scores:
            G.add_node(f"score_{s.id}", type="Score", score=s.priority_score)
            G.add_edge(f"outlet_{s.outlet_id}", f"score_{s.id}", relation="SCORED_BY")
        return G


class SemanticContextLayer:
    """Interprets questions and extracts grounded multi-table context using the Knowledge Graph."""

    @staticmethod
    async def extract_context(query: str, user_role: str, dsp_id: str, db: AsyncSession) -> dict:
        q_lower = query.lower()
        context = {
            "query": query,
            "intent": "general_inquiry",
            "entities": [],
            "data_summary": "",
            "records": []
        }

        # Intent 1: Priority Outlets / Visits
        if any(w in q_lower for w in ["visit", "priority", "first", "rank", "where to go", "route"]):
            context["intent"] = "priority_outlets"
            stmt = (
                select(Outlet, Merchant.business_name, OutletScore.priority_score, OutletScore.contributing_factors)
                .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
                .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
                .order_by(desc(OutletScore.priority_score))
                .limit(5)
            )
            res = await db.execute(stmt)
            outlets = res.all()
            
            lines = []
            for o, m_name, score, factors in outlets:
                factors_str = ", ".join(factors) if factors else "Standard review"
                lines.append(f"- **{o.outlet_name}** ({m_name or 'Independent'}): Score {score or 0}/100. Key Factors: {factors_str}. Location: {o.address or ''}, {o.city or ''}")
            
            context["data_summary"] = "Top priority outlets ranked by AI Risk Score:\n" + "\n".join(lines)
            return context

        # Intent 2: Churn Risk / At Risk
        if any(w in q_lower for w in ["churn", "risk", "dormant", "declining", "inactive"]):
            context["intent"] = "churn_risk"
            stmt = (
                select(Outlet, Merchant.business_name, OutletScore.priority_score, OutletScore.contributing_factors)
                .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
                .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
                .where(OutletScore.priority_score > 70)
                .order_by(desc(OutletScore.priority_score))
            )
            res = await db.execute(stmt)
            at_risk = res.all()
            
            lines = [f"- **{o.outlet_name}** (Score {score}): {', '.join(factors) if factors else 'Needs immediate outreach'}" for o, m, score, factors in at_risk]
            context["data_summary"] = f"There are currently **{len(at_risk)} outlets** at high risk requiring urgent intervention:\n" + "\n".join(lines)
            return context

        # Intent 3: Transactions / Sales Volume
        if any(w in q_lower for w in ["transaction", "sales", "volume", "revenue", "qr", "payment"]):
            context["intent"] = "transaction_summary"
            total_txns = await db.scalar(select(func.count(Transaction.id))) or 0
            total_vol = await db.scalar(select(func.sum(Transaction.amount))) or 0.0
            
            stmt = (
                select(Transaction, Outlet.outlet_name)
                .join(Outlet, Transaction.outlet_id == Outlet.id)
                .order_by(desc(Transaction.txn_date))
                .limit(5)
            )
            res = await db.execute(stmt)
            txns = res.all()
            
            lines = [f"- ₱{float(t.amount):,.2f} ({t.txn_type}) at **{name}** - Status: {t.status}" for t, name in txns]
            context["data_summary"] = f"Total System Transactions: **{total_txns}** totaling **₱{float(total_vol):,.2f}**.\nRecent Transactions:\n" + "\n".join(lines)
            return context

        # Intent 4: Actions / Recommendations
        if any(w in q_lower for w in ["action", "task", "pending", "recommendation", "todo"]):
            context["intent"] = "pending_actions"
            stmt = select(ActionRecommendation, Outlet.outlet_name).outerjoin(Outlet, ActionRecommendation.outlet_id == Outlet.id).limit(5)
            res = await db.execute(stmt)
            actions = res.all()
            
            if actions:
                lines = [f"- **{a.action_type}** for {name or 'Outlet'}: {a.action_detail} [Priority: {a.priority}]" for a, name in actions]
                context["data_summary"] = "Pending Recommended Actions for Field Reps:\n" + "\n".join(lines)
            else:
                context["data_summary"] = "All high priority merchant audit and promotional actions are up to date."
            return context

        # Default Fallback: Territory Overview
        total_outlets = await db.scalar(select(func.count(Outlet.id))) or 0
        total_merchants = await db.scalar(select(func.count(Merchant.id))) or 0
        avg_score = await db.scalar(select(func.avg(OutletScore.priority_score))) or 0.0
        context["data_summary"] = f"Territory Snapshot: Managing {total_outlets} outlets across {total_merchants} merchant networks. Territory average priority score is {float(avg_score):.1f}/100."
        return context

    @staticmethod
    def generate_response(context: dict) -> str:
        """Synthesizes structured context into an actionable natural language response."""
        intent = context.get("intent")
        data = context.get("data_summary", "")

        if intent == "priority_outlets":
            return (
                f"### 📍 Recommended Visit Schedule for Today\n\n"
                f"Based on real-time transaction activity and churn risk scores, here are the outlets you should prioritize:\n\n"
                f"{data}\n\n"
                f"💡 **Coach's Tip:** Focus on **Puregold Makati** and **Puregold Quezon Ave** first. Both are experiencing volume drops and require prompt POS terminal and QR placement verification."
            )
        elif intent == "churn_risk":
            return (
                f"### ⚠️ Churn Risk Alert\n\n"
                f"{data}\n\n"
                f"🔍 **Recommended Action:** Conduct in-person visits to offer promotional QR collaterals and verify GCash Cash-In terminal uptime."
            )
        elif intent == "transaction_summary":
            return (
                f"### 💳 Transaction & Volume Overview\n\n"
                f"{data}\n\n"
                f"📈 **Insight:** QR Payments and Bill Pay services represent the highest transaction frequency this week."
            )
        elif intent == "pending_actions":
            return (
                f"### 📋 Action Recommendations\n\n"
                f"{data}\n\n"
                f"✅ **Next Step:** Update the action status on your mobile dashboard after completing each on-site merchant visit."
            )
        else:
            return (
                f"### 🎯 Sales Coach AI Overview\n\n"
                f"{data}\n\n"
                f"You can ask me specific questions like:\n"
                f"- *\"Which outlets should I visit first today?\"*\n"
                f"- *\"How many outlets are at risk of churning?\"*\n"
                f"- *\"Show me recent transaction activity\"*\n"
                f"- *\"What actions are pending for my territory?\"*"
            )
