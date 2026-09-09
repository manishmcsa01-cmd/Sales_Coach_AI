import logging
import uuid
from datetime import date, datetime, timedelta
from sqlalchemy import select, func, update
from app.db.session import engine, AsyncSessionLocal
from app.models import (
    Base, Area, Merchant, Dsp, Outlet, OutletScore, Transaction, VisitLog,
    UserAccount, DspOutletAssignment, ActionRecommendation, Product, OutletProduct,
    Region, Province, CityMunicipality, Distributor, Manager, PosTerminal,
    QrCollateral, OperatingHours, MerchantCategory, MerchantKycDocument,
    MerchantBankAccount, MerchantContact, ScoringFeatureStore, MlModelRegistry,
    ModelDriftMetric, ActionCatalog, PitchPlaybook, ActionFeedbackLog,
    AuditLog, MerchandisingAuditItem, OutletPhoto, DailyOutletMetric, CashInLiquidityLog
)

logger = logging.getLogger(__name__)

async def seed_data_if_empty():
    """Seed initial sample data across all 35 enterprise tables idempotently."""
    async with AsyncSessionLocal() as session:
        try:
            # 1. Update legacy emails if any
            await session.execute(update(Dsp).where(Dsp.email == "dsp@test.com").values(email="dsp@salescoach.com"))
            await session.execute(update(Dsp).where(Dsp.email == "manager@test.com").values(email="manager@salescoach.com"))
            await session.execute(update(Dsp).where(Dsp.email == "admin@test.com").values(email="admin@salescoach.com"))
            await session.commit()

            # 2. Territory Hierarchy: Regions, Provinces, Cities
            reg_count = await session.scalar(select(func.count(Region.id)))
            if not reg_count or reg_count == 0:
                logger.info("Populating Regions, Provinces, and Cities...")
                r_ncr = Region(id=uuid.uuid4(), region_code="NCR", region_name="National Capital Region", island_group="Luzon")
                r_vis = Region(id=uuid.uuid4(), region_code="REG-VII", region_name="Central Visayas", island_group="Visayas")
                r_cal = Region(id=uuid.uuid4(), region_code="REG-IVA", region_name="CALABARZON", island_group="Luzon")
                session.add_all([r_ncr, r_vis, r_cal])
                await session.flush()

                p_mm = Province(id=uuid.uuid4(), region_id=r_ncr.id, province_name="Metro Manila", province_code="MM")
                p_cebu = Province(id=uuid.uuid4(), region_id=r_vis.id, province_name="Cebu", province_code="CEB")
                p_cav = Province(id=uuid.uuid4(), region_id=r_cal.id, province_name="Cavite", province_code="CAV")
                session.add_all([p_mm, p_cebu, p_cav])
                await session.flush()

                c_qc = CityMunicipality(id=uuid.uuid4(), province_id=p_mm.id, city_name="Quezon City", postal_code="1100", urban_tier="Metro_Tier1")
                c_mak = CityMunicipality(id=uuid.uuid4(), province_id=p_mm.id, city_name="Makati", postal_code="1200", urban_tier="Metro_Tier1")
                c_tag = CityMunicipality(id=uuid.uuid4(), province_id=p_mm.id, city_name="Taguig", postal_code="1630", urban_tier="Metro_Tier1")
                c_ceb = CityMunicipality(id=uuid.uuid4(), province_id=p_cebu.id, city_name="Cebu City", postal_code="6000", urban_tier="Urban_Tier2")
                session.add_all([c_qc, c_mak, c_tag, c_ceb])
                await session.flush()

            # 3. Areas
            area_count = await session.scalar(select(func.count(Area.id)))
            if not area_count or area_count == 0:
                logger.info("Populating Areas...")
                north = Area(id=uuid.uuid4(), area_name="Metro Manila North", region="NCR")
                south = Area(id=uuid.uuid4(), area_name="Metro Manila South", region="NCR")
                cebu = Area(id=uuid.uuid4(), area_name="Cebu Central", region="Visayas")
                session.add_all([north, south, cebu])
                await session.flush()

            areas = (await session.execute(select(Area))).scalars().all()
            north = next((a for a in areas if "North" in a.area_name), areas[0])
            south = next((a for a in areas if "South" in a.area_name), areas[1] if len(areas) > 1 else areas[0])
            cebu = next((a for a in areas if "Cebu" in a.area_name), areas[-1])

            # 4. Distributors
            dist_count = await session.scalar(select(func.count(Distributor.id)))
            if not dist_count or dist_count == 0:
                logger.info("Populating Distributors...")
                d1 = Distributor(id=uuid.uuid4(), company_name="Fast Logistics Field Sales Corp", tax_id="TIN-001-234-567", contact_person="Eduardo Santos", contact_email="eduardo@fastlogistics.ph", contact_phone="+63-917-555-0101", status="active")
                d2 = Distributor(id=uuid.uuid4(), company_name="Megawide Retail Solutions PH", tax_id="TIN-002-888-999", contact_person="Beatriz Cruz", contact_email="beatriz@megawide.ph", contact_phone="+63-917-555-0202", status="active")
                session.add_all([d1, d2])
                await session.flush()

            distributors = (await session.execute(select(Distributor))).scalars().all()
            d1 = distributors[0]

            # 5. Managers & DSPs
            dsp_count = await session.scalar(select(func.count(Dsp.id)))
            if not dsp_count or dsp_count == 0:
                logger.info("Populating DSPs...")
                dsp1 = Dsp(id=uuid.uuid4(), name="Juan Dela Cruz", email="dsp@salescoach.com", role="dsp", area_id=north.id, status="active", hire_date=date(2023, 1, 15))
                dsp2 = Dsp(id=uuid.uuid4(), name="Maria Santos", email="manager@salescoach.com", role="manager", area_id=south.id, status="active", hire_date=date(2022, 5, 10))
                dsp3 = Dsp(id=uuid.uuid4(), name="Pedro Reyes", email="admin@salescoach.com", role="admin", area_id=cebu.id, status="active", hire_date=date(2021, 3, 20))
                session.add_all([dsp1, dsp2, dsp3])
                await session.flush()

            dsps = (await session.execute(select(Dsp))).scalars().all()
            dsp1 = next((d for d in dsps if d.role == "dsp"), dsps[0])
            dsp2 = next((d for d in dsps if d.role == "manager"), dsps[1] if len(dsps) > 1 else dsps[0])
            dsp3 = next((d for d in dsps if d.role == "admin"), dsps[-1])

            mgr_count = await session.scalar(select(func.count(Manager.id)))
            if not mgr_count or mgr_count == 0:
                logger.info("Populating Area Managers...")
                m_south = Manager(id=uuid.uuid4(), full_name="Maria Santos", email="manager@salescoach.com", phone="+63-917-111-2222", area_id=south.id, distributor_id=d1.id, status="active", hire_date=date(2022, 5, 10))
                m_north = Manager(id=uuid.uuid4(), full_name="Carlos Mendoza", email="carlos.mendoza@salescoach.com", phone="+63-917-333-4444", area_id=north.id, distributor_id=d1.id, status="active", hire_date=date(2021, 8, 15))
                session.add_all([m_south, m_north])
                await session.flush()

            # 6. Merchant Categories
            cat_count = await session.scalar(select(func.count(MerchantCategory.id)))
            if not cat_count or cat_count == 0:
                logger.info("Populating Merchant Categories...")
                cat_super = MerchantCategory(id=uuid.uuid4(), category_code="FMCG-SUPER", category_name="Supermarket & Hypermarket", description="High-traffic grocery retail", benchmark_monthly_txns=2500, default_cash_in_fee_rate=0.0080)
                cat_conv = MerchantCategory(id=uuid.uuid4(), category_code="RET-CONV", category_name="Convenience Store", description="24/7 retail franchises", benchmark_monthly_txns=1200, default_cash_in_fee_rate=0.0100)
                cat_sari = MerchantCategory(id=uuid.uuid4(), category_code="RET-SARI", category_name="Sari-Sari Store", description="Micro neighborhood retail", benchmark_monthly_txns=400, default_cash_in_fee_rate=0.0120)
                cat_pharm = MerchantCategory(id=uuid.uuid4(), category_code="PHARM-DRUG", category_name="Pharmacy & Health", description="Drugstores and personal care", benchmark_monthly_txns=800, default_cash_in_fee_rate=0.0090)
                session.add_all([cat_super, cat_conv, cat_sari, cat_pharm])
                await session.flush()

            categories = (await session.execute(select(MerchantCategory))).scalars().all()

            # 7. Merchants
            m_count = await session.scalar(select(func.count(Merchant.id)))
            if not m_count or m_count == 0:
                logger.info("Populating Merchants...")
                m1 = Merchant(id=uuid.uuid4(), business_name="Puregold Price Club", owner_name="Lucio Co", business_type="Supermarket", kyc_status="verified", risk_tier="low", onboarded_date=date(2021, 6, 1))
                m2 = Merchant(id=uuid.uuid4(), business_name="7-Eleven Convenience", owner_name="Philippine Seven Corp", business_type="Convenience", kyc_status="verified", risk_tier="low", onboarded_date=date(2020, 11, 15))
                m3 = Merchant(id=uuid.uuid4(), business_name="Aling Nena Sari-Sari Store", owner_name="Elena Bautista", business_type="Retail", kyc_status="verified", risk_tier="medium", onboarded_date=date(2023, 3, 20))
                session.add_all([m1, m2, m3])
                await session.flush()

            merchants = (await session.execute(select(Merchant))).scalars().all()
            m1 = merchants[0]
            m2 = merchants[1] if len(merchants) > 1 else merchants[0]
            m3 = merchants[2] if len(merchants) > 2 else merchants[0]

            # 8. Merchant KYC, Bank Accounts, Contacts
            kyc_count = await session.scalar(select(func.count(MerchantKycDocument.id)))
            if not kyc_count or kyc_count == 0:
                logger.info("Populating Merchant KYC and Bank Accounts...")
                k1 = MerchantKycDocument(id=uuid.uuid4(), merchant_id=m1.id, document_type="SEC_Registration", document_number="SEC-CS2000-12345", verification_status="approved", verified_at=datetime.utcnow())
                k2 = MerchantKycDocument(id=uuid.uuid4(), merchant_id=m2.id, document_type="Mayors_Permit", document_number="QC-MP-2024-9988", verification_status="approved", verified_at=datetime.utcnow())
                k3 = MerchantKycDocument(id=uuid.uuid4(), merchant_id=m3.id, document_type="Barangay_Clearance", document_number="TAG-BRGY-4421", verification_status="approved", verified_at=datetime.utcnow())
                session.add_all([k1, k2, k3])

                b1 = MerchantBankAccount(id=uuid.uuid4(), merchant_id=m1.id, bank_name="BDO Unibank", account_number_mask="0012********4589", account_type="current", is_primary=True, status="active")
                b2 = MerchantBankAccount(id=uuid.uuid4(), merchant_id=m2.id, bank_name="BPI", account_number_mask="0039********8812", account_type="current", is_primary=True, status="active")
                b3 = MerchantBankAccount(id=uuid.uuid4(), merchant_id=m3.id, bank_name="GCash_Pro_Wallet", account_number_mask="0917******99", account_type="gcash_wallet", is_primary=True, status="active")
                session.add_all([b1, b2, b3])

                c1 = MerchantContact(id=uuid.uuid4(), merchant_id=m1.id, contact_name="Lucio Co", contact_role="Owner", phone_number="+63-917-888-0001", email="lucio@puregold.com.ph", is_primary_decision_maker=True)
                c2 = MerchantContact(id=uuid.uuid4(), merchant_id=m3.id, contact_name="Elena Bautista", contact_role="Owner", phone_number="+63-917-777-0003", email="elena@alingnena.com", is_primary_decision_maker=True)
                session.add_all([c1, c2])
                await session.flush()

            # 9. Outlets
            o_count = await session.scalar(select(func.count(Outlet.id)))
            if not o_count or o_count == 0:
                logger.info("Populating Outlets...")
                o1 = Outlet(id=uuid.uuid4(), merchant_id=m1.id, outlet_name="Puregold Quezon Ave", address="Quezon Ave cor Timog", city="Quezon City", region="NCR", outlet_type="Supermarket", status="active", area_id=north.id, onboarding_date=date(2021, 7, 1))
                o2 = Outlet(id=uuid.uuid4(), merchant_id=m2.id, outlet_name="7-Eleven Eastwood", address="Eastwood City Cyberpark", city="Quezon City", region="NCR", outlet_type="Convenience", status="active", area_id=north.id, onboarding_date=date(2020, 12, 1))
                o3 = Outlet(id=uuid.uuid4(), merchant_id=m1.id, outlet_name="Puregold Makati", address="Chino Roces Ave", city="Makati", region="NCR", outlet_type="Supermarket", status="active", area_id=south.id, onboarding_date=date(2021, 8, 1))
                o4 = Outlet(id=uuid.uuid4(), merchant_id=m3.id, outlet_name="Aling Nena Store Taguig", address="Signal Village", city="Taguig", region="NCR", outlet_type="Sari-Sari", status="active", area_id=south.id, onboarding_date=date(2023, 4, 1))
                o5 = Outlet(id=uuid.uuid4(), merchant_id=m2.id, outlet_name="7-Eleven Cebu IT Park", address="Salinas Dr Lahug", city="Cebu City", region="Visayas", outlet_type="Convenience", status="active", area_id=cebu.id, onboarding_date=date(2022, 2, 1))
                session.add_all([o1, o2, o3, o4, o5])
                await session.flush()

            outlets = (await session.execute(select(Outlet))).scalars().all()
            o1 = outlets[0]
            o2 = outlets[1] if len(outlets) > 1 else outlets[0]
            o3 = outlets[2] if len(outlets) > 2 else outlets[0]
            o4 = outlets[3] if len(outlets) > 3 else outlets[0]
            o5 = outlets[4] if len(outlets) > 4 else outlets[0]

            # 10. Operating Hours, POS Terminals, QR Collaterals
            pos_count = await session.scalar(select(func.count(PosTerminal.id)))
            if not pos_count or pos_count == 0:
                logger.info("Populating POS Terminals and Hardware...")
                pos1 = PosTerminal(id=uuid.uuid4(), outlet_id=o1.id, terminal_sn="POS-NCR-90211", device_model="Sunmi V2 Pro", firmware_version="v2.4.12", battery_health_pct=95, connectivity_type="4G_LTE", hardware_status="operational", last_heartbeat=datetime.utcnow())
                pos2 = PosTerminal(id=uuid.uuid4(), outlet_id=o2.id, terminal_sn="POS-NCR-90212", device_model="Pax A920", firmware_version="v3.1.0", battery_health_pct=68, connectivity_type="WiFi", hardware_status="scanner_fault", last_heartbeat=datetime.utcnow() - timedelta(hours=3))
                pos3 = PosTerminal(id=uuid.uuid4(), outlet_id=o3.id, terminal_sn="POS-NCR-90213", device_model="Sunmi V2 Pro", firmware_version="v2.4.12", battery_health_pct=92, connectivity_type="4G_LTE", hardware_status="operational", last_heartbeat=datetime.utcnow())
                session.add_all([pos1, pos2, pos3])

                qr1 = QrCollateral(id=uuid.uuid4(), outlet_id=o1.id, collateral_type="acrylic_standee", qr_payload_version="QRPh-v2", qr_code_id="QR-PG-QZN-001", condition="good", placement_location="counter_checkout", deployed_at=date(2023, 1, 10), last_inspected_at=date.today() - timedelta(days=14))
                qr2 = QrCollateral(id=uuid.uuid4(), outlet_id=o2.id, collateral_type="tent_card", qr_payload_version="QRPh-v2", qr_code_id="QR-711-EW-002", condition="torn", placement_location="counter_checkout", deployed_at=date(2022, 5, 20), last_inspected_at=date.today() - timedelta(days=2))
                qr3 = QrCollateral(id=uuid.uuid4(), outlet_id=o3.id, collateral_type="acrylic_standee", qr_payload_version="QRPh-v2", qr_code_id="QR-PG-MKT-003", condition="good", placement_location="counter_checkout", deployed_at=date(2023, 2, 15), last_inspected_at=date.today() - timedelta(days=5))
                qr4 = QrCollateral(id=uuid.uuid4(), outlet_id=o4.id, collateral_type="sticker_counter", qr_payload_version="QRPh-v2", qr_code_id="QR-NENA-TAG-004", condition="faded", placement_location="counter_checkout", deployed_at=date(2023, 4, 1), last_inspected_at=date.today() - timedelta(days=20))
                session.add_all([qr1, qr2, qr3, qr4])

                h1 = OperatingHours(id=uuid.uuid4(), outlet_id=o1.id, day_of_week=1, opening_time="08:00:00", closing_time="21:00:00", peak_traffic_window="17:00-19:30", is_24_hours=False)
                h2 = OperatingHours(id=uuid.uuid4(), outlet_id=o2.id, day_of_week=1, opening_time="00:00:00", closing_time="23:59:59", peak_traffic_window="12:00-14:00, 18:00-21:00", is_24_hours=True)
                session.add_all([h1, h2])
                await session.flush()

            # 11. Products & Outlet Products
            prod_count = await session.scalar(select(func.count(Product.id)))
            if not prod_count or prod_count == 0:
                logger.info("Populating Products...")
                p_qr = Product(id=uuid.uuid4(), product_name="GCash QR Payment", category="payments", description="Merchant QRPh payment acceptance", is_active=True)
                p_in = Product(id=uuid.uuid4(), product_name="GCash Cash-In", category="cash", description="Wallet top-up OTC for customers", is_active=True)
                p_out = Product(id=uuid.uuid4(), product_name="GCash Cash-Out", category="cash", description="OTC withdrawal from wallet", is_active=True)
                p_bills = Product(id=uuid.uuid4(), product_name="GCash Bills Pay", category="bills", description="Utility and bills settlement", is_active=True)
                p_cred = Product(id=uuid.uuid4(), product_name="GCredit Merchant Acceptance", category="lending", description="Revolving credit line checkout", is_active=True)
                session.add_all([p_qr, p_in, p_out, p_bills, p_cred])
                await session.flush()

            products = (await session.execute(select(Product))).scalars().all()
            p_qr = products[0]
            p_in = products[1] if len(products) > 1 else products[0]

            op_count = await session.scalar(select(func.count(OutletProduct.id)))
            if not op_count or op_count == 0:
                logger.info("Populating Outlet Product activations...")
                op1 = OutletProduct(id=uuid.uuid4(), outlet_id=o1.id, product_id=p_qr.id, status="active", commission_rate=0.0120, activated_date=date(2021, 7, 5))
                op2 = OutletProduct(id=uuid.uuid4(), outlet_id=o1.id, product_id=p_in.id, status="active", commission_rate=0.0100, activated_date=date(2021, 7, 5))
                op3 = OutletProduct(id=uuid.uuid4(), outlet_id=o4.id, product_id=p_in.id, status="active", commission_rate=0.0100, activated_date=date(2023, 4, 10))
                session.add_all([op1, op2, op3])
                await session.flush()

            # 12. Daily Metrics & Liquidity Float Logs
            liq_count = await session.scalar(select(func.count(CashInLiquidityLog.id)))
            if not liq_count or liq_count == 0:
                logger.info("Populating Liquidity Float Logs and Daily Metrics...")
                l1 = CashInLiquidityLog(id=uuid.uuid4(), outlet_id=o1.id, log_date=date.today(), opening_float=50000.0, closing_float=32000.0, float_stockout_occurred=False, replenishment_amount=0.0, replenishment_source="none")
                l2 = CashInLiquidityLog(id=uuid.uuid4(), outlet_id=o4.id, log_date=date.today(), opening_float=3000.0, closing_float=0.0, float_stockout_occurred=True, replenishment_amount=5000.0, replenishment_source="dsp_direct")
                session.add_all([l1, l2])

                m1_metric = DailyOutletMetric(id=uuid.uuid4(), outlet_id=o1.id, metric_date=date.today() - timedelta(days=1), total_gmv=125400.0, total_transactions=84, failed_transactions=2, unique_customers=79, avg_ticket_size=1492.85, cash_in_volume=45000.0, qr_payment_volume=80400.0)
                m2_metric = DailyOutletMetric(id=uuid.uuid4(), outlet_id=o4.id, metric_date=date.today() - timedelta(days=1), total_gmv=8200.0, total_transactions=19, failed_transactions=1, unique_customers=18, avg_ticket_size=431.50, cash_in_volume=6500.0, qr_payment_volume=1700.0)
                session.add_all([m1_metric, m2_metric])
                await session.flush()

            # 13. ML Model Registry & Drift Metrics
            ml_count = await session.scalar(select(func.count(MlModelRegistry.id)))
            if not ml_count or ml_count == 0:
                logger.info("Populating ML Model Registry and Drift Metrics...")
                model1 = MlModelRegistry(id=uuid.uuid4(), model_name="OutletPriorityXGB", model_version="v1.0.0", algorithm="XGBoost", auc_roc=0.8920, f1_score=0.8410, hyperparameters='{"n_estimators": 200, "max_depth": 6, "learning_rate": 0.05}', deployment_status="champion", deployed_at=datetime.utcnow() - timedelta(days=60))
                session.add(model1)
                await session.flush()

                d1_metric = ModelDriftMetric(id=uuid.uuid4(), model_id=model1.id, feature_name="gmv_wow_growth_pct", metric_type="PSI", metric_value=0.0820, threshold=0.2000, drift_detected=False, evaluated_at=datetime.utcnow())
                d2_metric = ModelDriftMetric(id=uuid.uuid4(), model_id=model1.id, feature_name="cash_in_stockout_count_7d", metric_type="KS_TEST", metric_value=0.2150, threshold=0.2000, drift_detected=True, evaluated_at=datetime.utcnow())
                session.add_all([d1_metric, d2_metric])
                await session.flush()

            # 14. Scoring Feature Store & Outlet Scores
            score_count = await session.scalar(select(func.count(OutletScore.id)))
            if not score_count or score_count == 0:
                logger.info("Populating Feature Store and Outlet Scores...")
                feat1 = ScoringFeatureStore(id=uuid.uuid4(), outlet_id=o1.id, days_since_last_txn=0, days_since_last_visit=5, gmv_wow_growth_pct=-12.5, gmv_mom_growth_pct=-8.0, cash_in_stockout_count_7d=0, qr_standee_damage_flag=False, pos_terminal_offline_hours_7d=0.0)
                feat2 = ScoringFeatureStore(id=uuid.uuid4(), outlet_id=o2.id, days_since_last_txn=1, days_since_last_visit=8, gmv_wow_growth_pct=-24.0, gmv_mom_growth_pct=-18.0, cash_in_stockout_count_7d=1, qr_standee_damage_flag=True, pos_terminal_offline_hours_7d=14.5)
                feat3 = ScoringFeatureStore(id=uuid.uuid4(), outlet_id=o4.id, days_since_last_txn=0, days_since_last_visit=18, gmv_wow_growth_pct=-32.0, gmv_mom_growth_pct=-28.0, cash_in_stockout_count_7d=4, qr_standee_damage_flag=True, pos_terminal_offline_hours_7d=0.0)
                session.add_all([feat1, feat2, feat3])

                s1 = OutletScore(id=uuid.uuid4(), outlet_id=o1.id, priority_score=88.5, contributing_factors=["declining_volume", "high_potential"], score_date=date.today(), model_version="v1.0")
                s2 = OutletScore(id=uuid.uuid4(), outlet_id=o2.id, priority_score=72.0, contributing_factors=["churn_risk", "hardware_issue"], score_date=date.today(), model_version="v1.0")
                s3 = OutletScore(id=uuid.uuid4(), outlet_id=o3.id, priority_score=94.0, contributing_factors=["dormant_merchant", "high_volume"], score_date=date.today(), model_version="v1.0")
                s4 = OutletScore(id=uuid.uuid4(), outlet_id=o4.id, priority_score=91.0, contributing_factors=["cash_in_stockout", "damaged_qr_standee"], score_date=date.today(), model_version="v1.0")
                s5 = OutletScore(id=uuid.uuid4(), outlet_id=o5.id, priority_score=60.0, contributing_factors=["new_merchant"], score_date=date.today(), model_version="v1.0")
                session.add_all([s1, s2, s3, s4, s5])
                await session.flush()

            # 15. Action Catalog & Pitch Playbooks
            cat_action_count = await session.scalar(select(func.count(ActionCatalog.id)))
            if not cat_action_count or cat_action_count == 0:
                logger.info("Populating Action Catalog and Playbooks...")
                ac1 = ActionCatalog(id=uuid.uuid4(), action_code="MERCH_AUDIT", action_name="Merchandising Collateral Audit & Swap", category="merchandising", recommended_duration_minutes=15, business_impact="high")
                ac2 = ActionCatalog(id=uuid.uuid4(), action_code="CASHIN_FLOAT", action_name="Cash-In Liquidity Replenishment", category="liquidity", recommended_duration_minutes=20, business_impact="critical")
                ac3 = ActionCatalog(id=uuid.uuid4(), action_code="POS_SWAP", action_name="POS Terminal Diagnostics & Swap", category="hardware", recommended_duration_minutes=25, business_impact="high")
                session.add_all([ac1, ac2, ac3])
                await session.flush()

                pb1 = PitchPlaybook(id=uuid.uuid4(), merchant_objection="Masyadong mataas ang transaction fee ng QR payments", recommended_pitch="Ipaliwanag na ang 1% MDR ay mas mura kaysa sa pamasahe papuntang bangko at cash leakage. May kasama ring libreng insurance protection mula sa GCash.", incentive_offer="Waiver ng MDR fee sa unang PHP 50,000 QR transactions ngayong buwan", effectiveness_rating=4.75)
                pb2 = PitchPlaybook(id=uuid.uuid4(), merchant_objection="Laging nauubusan ng Cash-In float kaya hindi maka-cater sa customer", recommended_pitch="Mag-set up ng Auto-Replenishment gamit ang BDO/BPI settlement link para hindi nauubusan ng pondo kapag payday weekend.", incentive_offer="PHP 500 cashback rebate kapag nag-maintain ng PHP 20,000 float sa buong linggo", effectiveness_rating=4.60)
                session.add_all([pb1, pb2])
                await session.flush()

            # 16. DSP Outlet Assignments
            as_count = await session.scalar(select(func.count(DspOutletAssignment.id)))
            if not as_count or as_count == 0:
                logger.info("Populating DSP Outlet Assignments...")
                as1 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp1.id, outlet_id=o1.id, assigned_date=date.today())
                as2 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp1.id, outlet_id=o2.id, assigned_date=date.today())
                as3 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp2.id, outlet_id=o3.id, assigned_date=date.today())
                as4 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp2.id, outlet_id=o4.id, assigned_date=date.today())
                as5 = DspOutletAssignment(id=uuid.uuid4(), dsp_id=dsp1.id, outlet_id=o3.id, assigned_date=date.today())
                session.add_all([as1, as2, as3, as4, as5])
                await session.flush()

            # 17. Action Recommendations & Feedback Logs
            act_count = await session.scalar(select(func.count(ActionRecommendation.id)))
            if not act_count or act_count == 0:
                logger.info("Populating Action Recommendations...")
                act1 = ActionRecommendation(id=uuid.uuid4(), outlet_id=o1.id, dsp_id=dsp1.id, action_type="Merchandising Audit", action_detail="Replace damaged GCash QR tent cards and stickers", priority="HIGH", status="pending")
                act2 = ActionRecommendation(id=uuid.uuid4(), outlet_id=o3.id, dsp_id=dsp2.id, action_type="Cash-In Training", action_detail="Train store clerk on Cash-In limit updates", priority="CRITICAL", status="completed")
                act3 = ActionRecommendation(id=uuid.uuid4(), outlet_id=o2.id, dsp_id=dsp1.id, action_type="POS Health Check", action_detail="Diagnose barcode scanner connectivity errors", priority="MEDIUM", status="completed")
                act4 = ActionRecommendation(id=uuid.uuid4(), outlet_id=o4.id, dsp_id=dsp2.id, action_type="Cash-In Float Boost", action_detail="Assist Aling Nena with PHP 5,000 float reload and replace faded counter sticker", priority="CRITICAL", status="pending")
                session.add_all([act1, act2, act3, act4])
                await session.flush()

                fb1 = ActionFeedbackLog(id=uuid.uuid4(), recommendation_id=act3.id, dsp_id=dsp1.id, is_accepted=True, feedback_notes="Hardware diagnostic performed; scanner optical glass was dirty and was successfully cleaned.", submitted_at=datetime.utcnow())
                session.add(fb1)
                await session.flush()

            # 18. Transactions
            t_count = await session.scalar(select(func.count(Transaction.id)))
            if not t_count or t_count == 0:
                logger.info("Populating Transactions...")
                now = datetime.utcnow()
                t1 = Transaction(id=uuid.uuid4(), outlet_id=o1.id, txn_type="QR_PAYMENT", amount=1500.0, txn_date=now, status="SUCCESS")
                t2 = Transaction(id=uuid.uuid4(), outlet_id=o2.id, txn_type="CASH_IN", amount=500.0, txn_date=now, status="SUCCESS")
                t3 = Transaction(id=uuid.uuid4(), outlet_id=o3.id, txn_type="BILL_PAY", amount=2300.0, txn_date=now, status="SUCCESS")
                t4 = Transaction(id=uuid.uuid4(), outlet_id=o4.id, txn_type="QR_PAYMENT", amount=250.0, txn_date=now, status="SUCCESS")
                t5 = Transaction(id=uuid.uuid4(), outlet_id=o5.id, txn_type="QR_PAYMENT", amount=890.0, txn_date=now, status="SUCCESS")
                session.add_all([t1, t2, t3, t4, t5])
                await session.flush()

            # 19. Visit Logs, Merchandising Audit Items & Outlet Photos
            v_count = await session.scalar(select(func.count(VisitLog.id)))
            if not v_count or v_count == 0:
                logger.info("Populating Visit Logs and Photo Audit Evidence...")
                now = datetime.utcnow()
                v1 = VisitLog(id=uuid.uuid4(), dsp_id=dsp1.id, outlet_id=o1.id, visit_date=now, visit_type="SCHEDULED", outcome="COMPLETED", notes="Marketing collaterals replaced", duration_minutes=25, check_in_lat=14.6349, check_in_lng=121.0345)
                v2 = VisitLog(id=uuid.uuid4(), dsp_id=dsp2.id, outlet_id=o3.id, visit_date=now, visit_type="AD_HOC", outcome="COMPLETED", notes="Assisted with QR scanner issue", duration_minutes=15, check_in_lat=14.5547, check_in_lng=121.0244)
                session.add_all([v1, v2])
                await session.flush()

                audit_item1 = MerchandisingAuditItem(id=uuid.uuid4(), visit_id=v1.id, audit_category="qr_visibility", is_compliant=True, action_taken="repositioned")
                audit_item2 = MerchandisingAuditItem(id=uuid.uuid4(), visit_id=v2.id, audit_category="sticker_cleanliness", is_compliant=False, deficiency_reason="torn_or_faded", action_taken="replaced_on_spot")
                session.add_all([audit_item1, audit_item2])

                photo1 = OutletPhoto(id=uuid.uuid4(), visit_id=v1.id, outlet_id=o1.id, photo_type="checkout_counter", photo_url="https://s3.ap-southeast-1.amazonaws.com/salescoach-evidence/outlets/o1-counter.jpg", ai_validation_label="Valid_GCash_Standee", ai_confidence_score=0.9650, captured_at=now)
                photo2 = OutletPhoto(id=uuid.uuid4(), visit_id=v2.id, outlet_id=o3.id, photo_type="damaged_collateral", photo_url="https://s3.ap-southeast-1.amazonaws.com/salescoach-evidence/outlets/o3-damaged-qr.jpg", ai_validation_label="Damaged_QR", ai_confidence_score=0.9120, captured_at=now)
                session.add_all([photo1, photo2])
                await session.flush()

            # 20. User Accounts & Audit Logs
            u_count = await session.scalar(select(func.count(UserAccount.id)))
            if not u_count or u_count == 0:
                logger.info("Populating User Accounts...")
                now = datetime.utcnow()
                u1 = UserAccount(id=uuid.uuid4(), email="admin@salescoach.com", password_hash="managed_by_cognito", role="admin", status="active", last_login=now)
                u2 = UserAccount(id=uuid.uuid4(), email="manager@salescoach.com", password_hash="managed_by_cognito", role="manager", status="active", last_login=now)
                u3 = UserAccount(id=uuid.uuid4(), email="dsp@salescoach.com", password_hash="managed_by_cognito", role="dsp", status="active", last_login=now)
                session.add_all([u1, u2, u3])
                await session.flush()

            u_admin = (await session.execute(select(UserAccount).where(UserAccount.role == "admin"))).scalar_one_or_none()
            if u_admin:
                audit1 = AuditLog(id=uuid.uuid4(), user_id=u_admin.id, action="SYSTEM_INIT_SEED", resource_type="database", resource_id="enterprise_35_tables", ip_address="127.0.0.1", user_agent="SalesCoachInitService/1.0", created_at=datetime.utcnow())
                session.add(audit1)

            await session.commit()
            logger.info("Successfully synchronized and seeded all 35 tables!")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error seeding database: {e}", exc_info=True)

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Successfully ensured all 35 database tables exist.")
        await seed_data_if_empty()
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
