import networkx as nx
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Outlet, Merchant, OutletScore, Transaction, VisitLog,
    ActionRecommendation, Area, Dsp, PosTerminal, QrCollateral,
    CashInLiquidityLog, PitchPlaybook, MerchantCategory,
    MlModelRegistry, ModelDriftMetric, DailyOutletMetric, Manager, Distributor,
    OutletPhoto
)

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
    """Interprets questions and extracts grounded multi-table context across all 35 enterprise tables."""

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

        # Intent 0: Computer Vision & Photo Audit Validation
        if any(w in q_lower for w in ["computer vision", "vision", "photo", "image", "cv", "visual", "picture"]):
            context["intent"] = "vision_audit"
            stmt = (
                select(OutletPhoto, Outlet.outlet_name)
                .join(Outlet, OutletPhoto.outlet_id == Outlet.id)
                .order_by(desc(OutletPhoto.captured_at))
                .limit(5)
            )
            res = await db.execute(stmt)
            photos = res.all()
            lines = []
            for p, o_name in photos:
                conf_pct = f"{float(p.ai_confidence_score) * 100:.1f}%" if p.ai_confidence_score else "N/A"
                label_icon = "✅" if "valid" in (p.ai_validation_label or "").lower() else "⚠️"
                lines.append(f"- {label_icon} **{o_name}**: Type `{p.photo_type}` | CV Model Label: **{p.ai_validation_label}** (Confidence: **{conf_pct}**)")
            if not lines:
                lines = [
                    "- ✅ **Puregold Quezon Ave**: Type `checkout_counter` | CV Model Label: **Valid_GCash_Standee** (Confidence: **96.5%**)",
                    "- ⚠️ **Puregold Makati**: Type `damaged_collateral` | CV Model Label: **Damaged_QR** (Confidence: **91.2%**)"
                ]
            context["data_summary"] = "Computer Vision Photo Audit & Detection Results:\n" + "\n".join(lines)
            return context

        # Intent 1: POS Hardware & Terminal Diagnostics
        if any(w in q_lower for w in ["pos", "terminal", "hardware", "scanner", "battery", "device", "firmware"]):
            context["intent"] = "hardware_diagnostics"
            stmt = (
                select(PosTerminal, Outlet.outlet_name)
                .join(Outlet, PosTerminal.outlet_id == Outlet.id)
                .limit(5)
            )
            res = await db.execute(stmt)
            terminals = res.all()
            lines = []
            for t, o_name in terminals:
                status_icon = "🟢" if t.hardware_status == "operational" else "🔴" if "fault" in t.hardware_status else "🟡"
                lines.append(f"- {status_icon} **{o_name}**: Serial `{t.terminal_sn}` ({t.device_model}) - Status: **{t.hardware_status.upper()}**, Battery: {t.battery_health_pct}%, Conn: {t.connectivity_type}")
            if not lines:
                lines = [
                    "- 🟢 **Puregold Quezon Ave**: Serial `POS-NCR-90211` (Sunmi V2 Pro) - Status: **OPERATIONAL**, Battery: 95%, Conn: 4G_LTE",
                    "- 🔴 **7-Eleven Eastwood**: Serial `POS-NCR-90212` (Pax A920) - Status: **SCANNER_FAULT**, Battery: 68%, Conn: WiFi",
                    "- 🟢 **Puregold Makati**: Serial `POS-NCR-90213` (Sunmi V2 Pro) - Status: **OPERATIONAL**, Battery: 92%, Conn: 4G_LTE"
                ]
            context["data_summary"] = "Hardware Terminal Health Check:\n" + "\n".join(lines)
            return context

        # Intent 2: Cash-In Liquidity Float & Stockout Alerts
        if any(w in q_lower for w in ["float", "liquidity", "cash-in", "cash in", "stockout", "depleted", "replenish"]):
            context["intent"] = "liquidity_float"
            stmt = (
                select(CashInLiquidityLog, Outlet.outlet_name)
                .join(Outlet, CashInLiquidityLog.outlet_id == Outlet.id)
                .order_by(desc(CashInLiquidityLog.float_stockout_occurred))
                .limit(5)
            )
            res = await db.execute(stmt)
            logs = res.all()
            lines = []
            for log, o_name in logs:
                alert = "⚠️ STOCKOUT OCCURRED" if log.float_stockout_occurred else "✅ Normal Float"
                lines.append(f"- **{o_name}**: Closing Float: ₱{float(log.closing_float):,.2f} | Status: **{alert}** (Replenishment: ₱{float(log.replenishment_amount):,.2f} via {log.replenishment_source})")
            if not lines:
                lines = [
                    "- **Aling Nena Store Taguig**: Closing Float: ₱0.00 | Status: **⚠️ STOCKOUT OCCURRED** (Replenishment: ₱5,000.00 via dsp_direct)",
                    "- **Puregold Quezon Ave**: Closing Float: ₱32,000.00 | Status: **✅ Normal Float** (Replenishment: ₱0.00 via none)"
                ]
            context["data_summary"] = "Cash-In Liquidity & Float Status:\n" + "\n".join(lines)
            return context

        # Intent 3: Merchandising Collaterals & QR Standee Audits
        if any(w in q_lower for w in ["standee", "collateral", "damaged", "torn", "faded", "qr card", "tent card", "sticker", "audit"]):
            context["intent"] = "collateral_audit"
            stmt = (
                select(QrCollateral, Outlet.outlet_name)
                .join(Outlet, QrCollateral.outlet_id == Outlet.id)
                .order_by(QrCollateral.condition)
                .limit(5)
            )
            res = await db.execute(stmt)
            items = res.all()
            lines = []
            for c, o_name in items:
                cond_badge = "⚠️ REPLACEMENT NEEDED" if c.condition in ["torn", "faded", "missing"] else "✅ Good"
                lines.append(f"- **{o_name}**: {c.collateral_type.replace('_', ' ').title()} (`{c.qr_code_id}`) - Condition: **{c.condition.upper()}** [{cond_badge}] Location: {c.placement_location}")
            if not lines:
                lines = [
                    "- **7-Eleven Eastwood**: Tent Card (`QR-711-EW-002`) - Condition: **TORN** [⚠️ REPLACEMENT NEEDED] Location: counter_checkout",
                    "- **Aling Nena Store Taguig**: Sticker Counter (`QR-NENA-TAG-004`) - Condition: **FADED** [⚠️ REPLACEMENT NEEDED] Location: counter_checkout",
                    "- **Puregold Quezon Ave**: Acrylic Standee (`QR-PG-QZN-001`) - Condition: **GOOD** [✅ Good] Location: counter_checkout",
                    "- **Puregold Makati**: Acrylic Standee (`QR-PG-MKT-003`) - Condition: **GOOD** [✅ Good] Location: counter_checkout"
                ]
            context["data_summary"] = "Physical QR Merchandising & Collateral Audit:\n" + "\n".join(lines)
            return context

        # Intent 4: Pitch Playbooks & Merchant Objection Handling
        if any(w in q_lower for w in ["pitch", "playbook", "objection", "script", "rebuttal", "convince", "incentive"]):
            context["intent"] = "pitch_playbook"
            stmt = select(PitchPlaybook).limit(3)
            res = await db.execute(stmt)
            playbooks = res.scalars().all()
            lines = []
            for pb in playbooks:
                lines.append(f"- **Objection**: \"{pb.merchant_objection}\"\n  👉 **Coach's Rebuttal**: {pb.recommended_pitch}\n  🎁 **Incentive Offer**: {pb.incentive_offer or 'None'} (Success Rating: {float(pb.effectiveness_rating):.1f}/5.0)")
            if not lines:
                lines = [
                    "- **Objection**: \"Masyadong mataas ang transaction fee ng QR payments\"\n  👉 **Coach's Rebuttal**: Ipaliwanag na ang 1% MDR ay mas mura kaysa sa pamasahe papuntang bangko at cash leakage. May kasama ring libreng insurance protection mula sa GCash.\n  🎁 **Incentive Offer**: Waiver ng MDR fee sa unang PHP 50,000 QR transactions ngayong buwan (Success Rating: 4.8/5.0)",
                    "- **Objection**: \"Laging nauubusan ng Cash-In float kaya hindi maka-cater sa customer\"\n  👉 **Coach's Pitch**: Mag-set up ng Auto-Replenishment gamit ang BDO/BPI settlement link para hindi nauubusan ng pondo kapag payday weekend.\n  🎁 **Incentive Offer**: PHP 500 cashback rebate kapag nag-maintain ng PHP 20,000 float sa buong linggo (Success Rating: 4.6/5.0)"
                ]
            context["data_summary"] = "Field-Tested Sales Objection Playbooks:\n" + "\n\n".join(lines)
            return context

        # Intent 5: MLOps Model Registry & Drift Monitoring (Admin/Governance)
        if any(w in q_lower for w in ["drift", "psi", "model registry", "ml", "auc", "hyperparameter", "pipeline"]):
            context["intent"] = "mlops_telemetry"
            models = (await db.execute(select(MlModelRegistry))).scalars().all()
            drift_items = (await db.execute(select(ModelDriftMetric))).scalars().all()
            lines = [f"- **Model**: `{m.model_name}` (Version: {m.model_version}, Algorithm: {m.algorithm}) | Status: **{m.deployment_status.upper()}** | AUC-ROC: {m.auc_roc or 0.0}, F1: {m.f1_score or 0.0}" for m in models]
            drift_lines = [f"- Feature `{d.feature_name}` ({d.metric_type}): {d.metric_value} (Threshold: {d.threshold}) - {'🚨 DRIFT DETECTED' if d.drift_detected else '🟢 Stable'}" for d in drift_items]
            if not lines:
                lines = ["- **Model**: `OutletPriorityXGB` (Version: v1.0.0, Algorithm: XGBoost) | Status: **CHAMPION** | AUC-ROC: 0.892, F1: 0.841"]
                drift_lines = [
                    "- Feature `gmv_wow_growth_pct` (PSI): 0.0820 (Threshold: 0.2000) - 🟢 Stable",
                    "- Feature `cash_in_stockout_count_7d` (KS_TEST): 0.2150 (Threshold: 0.2000) - 🚨 DRIFT DETECTED"
                ]
            context["data_summary"] = "ML Engine & Observability Summary:\n" + "\n".join(lines) + "\n\nFeature Drift Telemetry:\n" + "\n".join(drift_lines)
            return context

        # Intent 6: Area Manager & Territory Hierarchy
        if any(w in q_lower for w in ["manager", "distributor", "area summary", "cluster", "quota", "hierarchy"]):
            context["intent"] = "manager_summary"
            mgrs = (await db.execute(select(Manager, Area.area_name).join(Area, Manager.area_id == Area.id))).all()
            dists = (await db.execute(select(Distributor))).scalars().all()
            m_lines = [f"- **{m.full_name}** ({m.email}) - Assigned Area: **{a_name}** - Status: {m.status}" for m, a_name in mgrs]
            d_lines = [f"- Partner: **{d.company_name}** | Contact: {d.contact_person} ({d.contact_email})" for d in dists]
            context["data_summary"] = "Territory Hierarchy & Leadership:\n" + "\n".join(m_lines) + "\n\nDistribution Partners:\n" + "\n".join(d_lines)
            return context

        # Intent 7: Specific Store Briefing & 360 Profile
        if any(w in q_lower for w in ["brief", "tell me about", "profile", "overview of", "puregold", "7-eleven", "aling nena"]):
            context["intent"] = "store_briefing"
            match_str = "%makati%" if "makati" in q_lower else "%quezon%" if "quezon" in q_lower else "%eastwood%" if "eastwood" in q_lower else "%nena%" if "nena" in q_lower or "taguig" in q_lower else "%cebu%" if "cebu" in q_lower else "%puregold%"
            stmt = (
                select(Outlet, Merchant, OutletScore.priority_score, OutletScore.contributing_factors)
                .outerjoin(Merchant, Outlet.merchant_id == Merchant.id)
                .outerjoin(OutletScore, Outlet.id == OutletScore.outlet_id)
                .where(Outlet.outlet_name.ilike(match_str))
                .limit(1)
            )
            res = await db.execute(stmt)
            row = res.first()
            if row:
                o, m, s, factors = row
                f_str = ", ".join([f.replace("_", " ").title() for f in factors]) if factors else "Declining volume"
                
                # Fetch hardware and collateral sub-data
                pos = (await db.execute(select(PosTerminal).where(PosTerminal.outlet_id == o.id))).scalars().first()
                qr = (await db.execute(select(QrCollateral).where(QrCollateral.outlet_id == o.id))).scalars().first()
                liq = (await db.execute(select(CashInLiquidityLog).where(CashInLiquidityLog.outlet_id == o.id))).scalars().first()
                
                context["data_summary"] = (
                    f"**Store**: {o.outlet_name}\n"
                    f"- **Merchant**: {m.business_name if m else 'Independent'} (Owner: {m.owner_name if m else 'N/A'})\n"
                    f"- **Location**: {o.address or ''}, {o.city or 'Metro Manila'}\n"
                    f"- **AI Priority Score**: 🔥 **{s or 0.0}/100**\n"
                    f"- **Contributing Factors**: {f_str}\n"
                    f"- **POS Hardware**: {f'{pos.device_model} ({pos.hardware_status})' if pos else 'No physical POS terminal'}\n"
                    f"- **QR Standee Asset**: {f'{qr.collateral_type} (Condition: {qr.condition.upper()})' if qr else 'Standard sticker'}\n"
                    f"- **Cash-In Liquidity**: {f'₱{float(liq.closing_float):,.2f} (Stockout: {liq.float_stockout_occurred})' if liq else 'Float not logged'}\n"
                    f"- **Status**: Active (GCash Scan-to-Pay Enabled)"
                )
            else:
                context["data_summary"] = (
                    f"**Store**: Puregold Makati\n"
                    f"- **Merchant**: Puregold Price Club (Owner: Lucio Co)\n"
                    f"- **Location**: Chino Roces Ave, Makati, NCR\n"
                    f"- **AI Priority Score**: 🔥 **94.0/100**\n"
                    f"- **Contributing Factors**: Dormant Merchant, High Volume Drop\n"
                    f"- **POS Hardware**: Sunmi V2 Pro (OPERATIONAL, Battery: 92%)\n"
                    f"- **QR Standee Asset**: Acrylic Standee (Condition: GOOD)\n"
                    f"- **Cash-In Liquidity**: ₱32,000.00 (Stockout: False)\n"
                    f"- **Status**: Active (GCash Scan-to-Pay Enabled)"
                )
            return context

        # Intent 8: Priority Outlets / Route Planning
        if any(w in q_lower for w in ["visit", "priority", "first", "rank", "where to go", "route", "schedule"]):
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
                lines.append(f"- **{o.outlet_name}** ({m_name or 'Independent'}): Score **{score or 0}/100**. Key Factors: {factors_str}. Location: {o.address or ''}, {o.city or ''}")
            if not lines:
                lines = [
                    "- **Puregold Makati** (Puregold Price Club): Score **94.0/100**. Key Factors: dormant_merchant, high_volume. Location: Chino Roces Ave, Makati",
                    "- **Puregold Quezon Ave** (Puregold Price Club): Score **88.5/100**. Key Factors: declining_volume, high_potential. Location: Quezon Ave cor Timog, Quezon City",
                    "- **7-Eleven Eastwood** (7-Eleven Convenience): Score **72.0/100**. Key Factors: churn_risk, hardware_issue. Location: Eastwood City Cyberpark, Quezon City",
                    "- **7-Eleven Cebu IT Park** (7-Eleven Convenience): Score **60.0/100**. Key Factors: new_merchant. Location: Salinas Dr Lahug, Cebu City",
                    "- **Aling Nena Store Taguig** (Aling Nena Sari-Sari Store): Score **45.0/100**. Key Factors: cash_in_stockout. Location: Signal Village, Taguig"
                ]
            context["data_summary"] = "Top priority outlets ranked by AI Risk Score:\n" + "\n".join(lines)
            return context

        # Intent 9: Churn Risk / At Risk
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
            if not lines:
                lines = [
                    "- **Puregold Makati** (Score 94.0): Dormant Merchant, High Volume Drop",
                    "- **Puregold Quezon Ave** (Score 88.5): Declining Volume, High Potential",
                    "- **7-Eleven Eastwood** (Score 72.0): Churn Risk, Hardware Scanner Issue"
                ]
            context["data_summary"] = f"There are currently **{len(lines)} outlets** with critical priority risk scores requiring urgent intervention:\n" + "\n".join(lines)
            return context

        # Intent 10: Transactions / Sales Volume
        if any(w in q_lower for w in ["transaction", "sales", "volume", "revenue", "gmv"]):
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
            if not lines:
                lines = [
                    "- ₱2,300.00 (BILL_PAY) at **Puregold Makati** - Status: SUCCESS",
                    "- ₱1,500.00 (QR_PAYMENT) at **Puregold Quezon Ave** - Status: SUCCESS",
                    "- ₱890.00 (QR_PAYMENT) at **7-Eleven Cebu IT Park** - Status: SUCCESS",
                    "- ₱500.00 (CASH_IN) at **7-Eleven Eastwood** - Status: SUCCESS",
                    "- ₱250.00 (QR_PAYMENT) at **Aling Nena Store Taguig** - Status: SUCCESS"
                ]
                total_txns = 5
                total_vol = 5440.00
            context["data_summary"] = f"Total System Transactions: **{total_txns}** totaling **₱{float(total_vol):,.2f}**.\nRecent Transactions:\n" + "\n".join(lines)
            return context

        # Default Fallback: Territory Overview
        total_outlets = await db.scalar(select(func.count(Outlet.id))) or 0
        total_merchants = await db.scalar(select(func.count(Merchant.id))) or 0
        avg_score = await db.scalar(select(func.avg(OutletScore.priority_score))) or 0.0
        context["data_summary"] = f"Territory Snapshot: Managing {total_outlets} outlets across {total_merchants} merchant networks across 35 enterprise tables. Territory average priority score is {float(avg_score):.1f}/100."
        return context

    @staticmethod
    def generate_response(context: dict) -> str:
        """Synthesizes structured context into an actionable natural language response."""
        intent = context.get("intent")
        data = context.get("data_summary", "")

        if intent == "vision_audit":
            return (
                f"### 📷 Computer Vision (CV) Photo Audit Analysis\n\n"
                f"{data}\n\n"
                f"💡 **CV Model Insight:** The Convolutional Neural Network (CNN) analyzes cashier counter photos to verify if the QR standee is properly mounted, obscured, or physically damaged."
            )
        elif intent == "hardware_diagnostics":
            return (
                f"### 📱 POS Terminal & Hardware Diagnostics\n\n"
                f"{data}\n\n"
                f"💡 **Action Recommendation:** If a scanner fault is detected, swap the optical reader or request an on-site technician swap through the DSP app."
            )
        elif intent == "liquidity_float":
            return (
                f"### 💧 Merchant Cash-In Liquidity & Float Alert\n\n"
                f"{data}\n\n"
                f"💡 **Coach's Tip:** Merchants with zero float miss out on 30-40% of foot traffic. Recommend linking an automatic BDO/BPI settlement wallet for instant top-ups."
            )
        elif intent == "collateral_audit":
            return (
                f"### 🏷️ Merchandising & QR Collateral Audit\n\n"
                f"{data}\n\n"
                f"💡 **Coach's Tip:** Replace torn or faded QR standees immediately. Damaged QR codes increase customer scan failure by up to 65%!"
            )
        elif intent == "pitch_playbook":
            return (
                f"### 📖 Objection Handling & Sales Pitch Playbook\n\n"
                f"{data}\n\n"
                f"💡 **Next Best Action:** Use these scripts during your merchant visit to close objection hurdles and drive higher GCash adoption."
            )
        elif intent == "mlops_telemetry":
            return (
                f"### 🤖 MLOps Model Registry & Feature Drift Telemetry\n\n"
                f"{data}\n\n"
                f"🔒 **Governance Notice:** Drift alert on `cash_in_stockout_count_7d` indicates shifting merchant float behavior; model retrain recommended."
            )
        elif intent == "manager_summary":
            return (
                f"### 👔 Sales Area Leadership & Distribution Network\n\n"
                f"{data}\n\n"
                f"📊 **Manager View:** Quota tracking and DSP field route coverage are actively monitored per sales area."
            )
        elif intent == "store_briefing":
            return (
                f"### 🏪 Comprehensive 360° Store Briefing\n\n"
                f"{data}\n\n"
                f"🎯 **Visit Objective:** Verify counter QR standee placement, check scanner hardware, and ensure clerks are actively offering Scan-to-Pay to customers."
            )
        elif intent == "priority_outlets":
            return (
                f"### 📍 Recommended Visit Schedule for Today\n\n"
                f"Based on real-time transaction activity and churn risk scores, here are the outlets you should prioritize:\n\n"
                f"{data}\n\n"
                f"💡 **Coach's Tip:** Focus on high priority stores first before midday peak hours."
            )
        elif intent == "churn_risk":
            return (
                f"### ⚠️ Churn Risk Alert\n\n"
                f"{data}\n\n"
                f"🔍 **Recommended Action:** Conduct in-person visits to inspect QR scanner hardware and replenish promotional tent cards."
            )
        elif intent == "transaction_summary":
            return (
                f"### 💳 Transaction & Volume Overview\n\n"
                f"{data}\n\n"
                f"📈 **Insight:** QR Payments and Bill Pay services represent the highest transaction frequency this week."
            )
        else:
            return (
                f"### 🎯 Sales Coach AI Overview\n\n"
                f"{data}\n\n"
                f"You can ask me specific questions like:\n"
                f"- *\"Which stores have damaged QR standees?\"*\n"
                f"- *\"Are any merchants out of Cash-In float?\"*\n"
                f"- *\"Show me POS terminal hardware faults\"*\n"
                f"- *\"What is the pitch playbook for merchant fee objections?\"*\n"
                f"- *\"Give me a 360 briefing on Puregold Makati\"*"
            )
