"""Generate REALISTIC GCash-aligned CSV dataset files."""
import csv
import os
import uuid
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

fake = Faker()
random.seed(42)

OUTPUT_DIR = Path(__file__).parent / "csv"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# Philippine Cities & Provinces (Real GCash Markets)
# ============================================================
PH_LOCATIONS = [
    # NCR
    ("Quezon City", "Metro Manila"), ("Manila", "Metro Manila"), ("Makati", "Metro Manila"),
    ("Pasig", "Metro Manila"), ("Taguig", "Metro Manila"), ("Mandaluyong", "Metro Manila"),
    ("Caloocan", "Metro Manila"), ("Parañaque", "Metro Manila"), ("Las Piñas", "Metro Manila"),
    ("Muntinlupa", "Metro Manila"), ("Marikina", "Metro Manila"), ("Valenzuela", "Metro Manila"),
    ("Navotas", "Metro Manila"), ("San Juan", "Metro Manila"), ("Malabon", "Metro Manila"),
    # Visayas
    ("Cebu City", "Cebu"), ("Mandaue", "Cebu"), ("Lapu-Lapu", "Cebu"),
    ("Iloilo City", "Iloilo"), ("Bacolod", "Negros Occidental"), ("Tacloban", "Leyte"),
    # Mindanao
    ("Davao City", "Davao del Sur"), ("Cagayan de Oro", "Misamis Oriental"),
    ("Zamboanga City", "Zamboanga del Sur"), ("General Santos", "South Cotabato"),
    # Central Luzon
    ("Angeles", "Pampanga"), ("San Fernando", "Pampanga"), ("Olongapo", "Zambales"),
    ("Meycauayan", "Bulacan"), ("Malolos", "Bulacan"),
    # CALABARZON
    ("Antipolo", "Rizal"), ("Bacoor", "Cavite"), ("Imus", "Cavite"),
    ("Dasmariñas", "Cavite"), ("Santa Rosa", "Laguna"), ("Calamba", "Laguna"),
]

# Philippine street names
PH_STREETS = [
    "Rizal Street", "Bonifacio Avenue", "Mabini Street", "Quezon Avenue", "EDSA",
    "Commonwealth Ave", "Marcos Highway", "Katipunan Ave", "Aurora Blvd", "España Blvd",
    "Taft Avenue", "Roxas Blvd", "Osmena Blvd", "Colon Street", "Fuente Osmena",
    "J.P. Laurel Ave", "MacArthur Highway", "Aguinaldo Highway", "Gov. Drive",
    "National Highway", "Provincial Road", "Barangay Road", "Purok 1 Street",
]

# Filipino names
PH_FIRST_NAMES_M = ["Juan", "Jose", "Pedro", "Carlos", "Miguel", "Roberto", "Antonio", "Eduardo", "Ricardo", "Fernando", "Ramon", "Reynaldo", "Danilo", "Ernesto", "Rolando"]
PH_FIRST_NAMES_F = ["Maria", "Ana", "Rosa", "Elena", "Carmen", "Luz", "Gloria", "Teresa", "Josefina", "Rosario", "Lorna", "Nelia", "Corazon", "Fe", "Erlinda"]
PH_LAST_NAMES = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Garcia", "Mendoza", "Torres", "Tomas", "Andrade", "Ramos", "Aquino", "Rivera", "Flores", "Lopez", "Gonzales", "Hernandez", "Villanueva", "Castro", "Dela Cruz"]

def ph_name():
    first = random.choice(PH_FIRST_NAMES_M + PH_FIRST_NAMES_F)
    last = random.choice(PH_LAST_NAMES)
    return f"{first} {last}"

def ph_phone():
    prefix = random.choice(["917", "918", "919", "920", "921", "926", "927", "928", "929", "930", "935", "936", "945", "946", "950", "955", "956", "961", "966", "975", "977"])
    return f"+63 {prefix} {random.randint(100,999)} {random.randint(1000,9999)}"

def ph_address():
    return f"{random.randint(1,999)} {random.choice(PH_STREETS)}, Brgy. {random.choice(['San Antonio', 'Poblacion', 'Santo Niño', 'San Jose', 'San Isidro', 'Bagong Silang', 'Kamuning', 'Pinyahan', 'Ugong', 'Bambang'])}"

GEN_DATE = datetime(2025, 8, 1)

# ============================================================
# Reference Data
# ============================================================
AREAS = [
    {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"area-{i}")), "area_name": name, "region": region}
    for i, (name, region) in enumerate([
        ("Metro Manila North", "NCR"), ("Metro Manila South", "NCR"),
        ("Cebu", "Visayas"), ("Davao", "Mindanao"), ("Pampanga", "Central Luzon")
    ])
]

PRODUCTS = [
    {"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"prod-{i}")), "product_name": name, "product_code": code, "category": cat}
    for i, (name, code, cat) in enumerate([
        ("GCash Cash-In", "GCIN", "cash"), ("GCash Cash-Out", "GCOUT", "cash"),
        ("Bills Payment", "BILLS", "payments"), ("Buy Load", "LOAD", "telco"),
        ("Send Money", "SEND", "transfer"), ("Pay QR", "QR", "payments"),
        ("GInsure", "GINS", "insurance"), ("GInvest", "GINV", "invest"),
        ("GCredit", "GCRD", "lending"), ("GSave", "GSAV", "savings")
    ])
]

# Area-to-city mapping
AREA_CITIES = {
    0: [l for l in PH_LOCATIONS if l[1] == "Metro Manila"][:8],   # MM North
    1: [l for l in PH_LOCATIONS if l[1] == "Metro Manila"][8:],    # MM South
    2: [l for l in PH_LOCATIONS if l[1] in ("Cebu", "Iloilo", "Negros Occidental", "Leyte")],
    3: [l for l in PH_LOCATIONS if l[1] in ("Davao del Sur", "Misamis Oriental", "Zamboanga del Sur", "South Cotabato")],
    4: [l for l in PH_LOCATIONS if l[1] in ("Pampanga", "Zambales", "Bulacan", "Rizal", "Cavite", "Laguna")],
}

# ============================================================
# Generate Managers & DSPs
# ============================================================
managers = []
for i, area in enumerate(AREAS):
    managers.append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"mgr-{i}")),
        "full_name": ph_name(),
        "email": f"manager{i+1}@gcash.com",
        "phone": ph_phone(),
        "area_id": area["id"],
        "status": "active",
        "hire_date": fake.date_between(start_date="-3y", end_date="-1y").isoformat()
    })

dsps = []
for i in range(40):
    area_idx = i % len(AREAS)
    area = AREAS[area_idx]
    mgr = managers[area_idx]
    dsps.append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"dsp-{i}")),
        "full_name": ph_name(),
        "email": f"dsp{i+1}@gcash.com",
        "phone": ph_phone(),
        "area_id": area["id"],
        "manager_id": mgr["id"],
        "status": random.choice(["active"] * 9 + ["inactive"]),
        "hire_date": fake.date_between(start_date="-2y", end_date="-3m").isoformat(),
        "daily_target_visits": random.randint(8, 15)
    })

# ============================================================
# Generate Merchants & Outlets (Philippine-realistic)
# ============================================================
SARI_SARI_NAMES = ["Aling {}'s Store", "Mang {}'s Tindahan", "{}'s Sari-Sari", "Tindahan ni {}", "{}'s Mini Mart"]
BUSINESS_NAMES = {
    "sari_sari_store": SARI_SARI_NAMES,
    "convenience_store": ["{} Express", "{} Convenience", "{} Mini Stop"],
    "pharmacy": ["{} Pharmacy", "{} Drug Store", "Botica ni {}"],
    "pawnshop": ["{} Pawnshop", "{} Lending", "Sangla ni {}"],
    "remittance_center": ["{} Remittance", "{} Padala Center"],
    "internet_cafe": ["{} Internet Cafe", "{} Pisong Net", "{}'s Computer Shop"],
}

# Sari-sari stores should dominate (~50%) - realistic for Philippines
BUSINESS_TYPE_WEIGHTS = {
    "sari_sari_store": 50,
    "convenience_store": 12,
    "pharmacy": 10,
    "pawnshop": 10,
    "remittance_center": 10,
    "internet_cafe": 8,
}
BUSINESS_TYPES_WEIGHTED = []
for bt, w in BUSINESS_TYPE_WEIGHTS.items():
    BUSINESS_TYPES_WEIGHTED.extend([bt] * w)

merchants = []
for i in range(200):
    btype = random.choice(BUSINESS_TYPES_WEIGHTED)
    owner = ph_name()
    first_name = owner.split()[0]
    bname = random.choice(BUSINESS_NAMES[btype]).format(first_name)
    merchants.append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"merch-{i}")),
        "business_name": bname,
        "owner_name": owner,
        "contact_number": ph_phone(),
        "business_type": btype,
        "registration_date": fake.date_between(start_date="-3y", end_date="-6m").isoformat(),
        "status": random.choice(["active"] * 8 + ["suspended", "inactive"])
    })

outlets = []
OUTLET_STATUSES = ["active"] * 65 + ["inactive"] * 10 + ["at_risk"] * 15 + ["churned"] * 10
for i in range(708):
    area_idx = i % len(AREAS)
    area = AREAS[area_idx]
    merch = merchants[i % len(merchants)]
    cities = AREA_CITIES.get(area_idx, PH_LOCATIONS[:5])
    city, province = random.choice(cities)

    # Latitude/longitude realistic for Philippines (7-18 N, 117-127 E)
    lat_ranges = {"NCR": (14.45, 14.75), "Visayas": (10.2, 11.0), "Mindanao": (6.9, 7.5), "Central Luzon": (14.8, 15.5)}
    lat_range = lat_ranges.get(area["region"], (14.0, 15.0))
    lng_ranges = {"NCR": (120.9, 121.1), "Visayas": (123.8, 124.0), "Mindanao": (125.4, 125.7), "Central Luzon": (120.5, 120.8)}
    lng_range = lng_ranges.get(area["region"], (120.5, 121.0))

    outlets.append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"outlet-{i}")),
        "outlet_name": f"{merch['business_name']} - {city}" if i >= len(merchants) else merch['business_name'],
        "merchant_id": merch["id"],
        "area_id": area["id"],
        "address": ph_address(),
        "city": city,
        "province": province,
        "latitude": round(random.uniform(*lat_range), 6),
        "longitude": round(random.uniform(*lng_range), 6),
        "outlet_type": random.choice(["tier1_urban"] * 4 + ["tier2_suburban"] * 4 + ["tier3_rural"] * 2),
        "status": random.choice(OUTLET_STATUSES),
        "onboarding_date": fake.date_between(start_date="-2y", end_date="-1m").isoformat()
    })

# ============================================================
# Assignments
# ============================================================
assignments = []
for i, outlet in enumerate(outlets):
    area_dsps = [d for d in dsps if d["area_id"] == outlet["area_id"] and d["status"] == "active"]
    if area_dsps:
        dsp = area_dsps[i % len(area_dsps)]
        assignments.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"assign-{i}")),
            "dsp_id": dsp["id"],
            "outlet_id": outlet["id"],
            "assigned_date": fake.date_between(start_date="-1y", end_date="-1m").isoformat(),
            "status": "active"
        })

# ============================================================
# Outlet Scores
# ============================================================
scores = []
for outlet in outlets:
    # Score correlates with status
    if outlet["status"] == "active":
        base = random.uniform(15, 55)
    elif outlet["status"] == "at_risk":
        base = random.uniform(60, 85)
    elif outlet["status"] == "churned":
        base = random.uniform(80, 100)
    else:
        base = random.uniform(40, 70)

    factors = random.sample(["low_transaction_volume", "declining_revenue", "missed_visits", "product_gap", "competitor_risk", "high_churn_probability", "inactive_products"], k=random.randint(1, 3))
    scores.append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"score-{outlet['id']}")),
        "outlet_id": outlet["id"],
        "priority_score": round(base, 1),
        "transaction_score": round(random.uniform(max(0, base-30), min(100, base+20)), 1),
        "engagement_score": round(random.uniform(max(0, base-25), min(100, base+25)), 1),
        "product_adoption_score": round(random.uniform(10, 90), 1),
        "risk_score": round(random.uniform(max(0, base-20), min(100, base+10)), 1),
        "contributing_factors": "|".join(factors),
        "scored_at": (GEN_DATE - timedelta(days=random.randint(0, 7))).isoformat()
    })

# ============================================================
# Transactions — REALISTIC GCash volumes & amounts
# ============================================================
# Real GCash: active outlet does 20-50 txns/day
# For 708 outlets over 90 days with ~60% active: ~25 txns/day * 425 active outlets * 90 days = ~956K
# We'll generate 50,000 for manageable CSV size but with realistic distributions

TXN_CONFIG = {
    #  type:           weight, min_amt, max_amt, avg_amt
    "cash_in":         (30, 100, 20000, 2500),
    "cash_out":        (25, 100, 15000, 2000),
    "buy_load":        (20, 10, 500, 50),       # Prepaid load: PHP 10-500
    "bills_payment":   (12, 200, 10000, 1500),
    "send_money":      (8, 50, 10000, 1200),
    "pay_qr":          (5, 20, 3000, 350),       # Small retail QR payments
}

txn_types_weighted = []
for ttype, (weight, _, _, _) in TXN_CONFIG.items():
    txn_types_weighted.extend([ttype] * weight)

transactions = []
active_outlets = [o for o in outlets if o["status"] in ("active", "at_risk")]

for i in range(50000):
    outlet = random.choice(active_outlets)
    txn_type = random.choice(txn_types_weighted)
    _, min_a, max_a, avg_a = TXN_CONFIG[txn_type]

    # Skewed distribution towards average (more realistic)
    amount = round(max(min_a, min(max_a, random.gauss(avg_a, avg_a * 0.6))), 2)

    txn_date = GEN_DATE - timedelta(days=random.randint(0, 90), hours=random.randint(6, 22), minutes=random.randint(0, 59))
    transactions.append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"txn-{i}")),
        "outlet_id": outlet["id"],
        "txn_type": txn_type,
        "amount": amount,
        "currency": "PHP",
        "txn_date": txn_date.isoformat(),
        "status": random.choices(["completed", "failed", "reversed"], weights=[92, 5, 3])[0]
    })

# ============================================================
# Visit Logs — REALISTIC frequency (8-15 visits/DSP/day)
# ============================================================
visits = []
active_dsps = [d for d in dsps if d["status"] == "active"]

for day_offset in range(60):
    visit_date = GEN_DATE - timedelta(days=day_offset)
    if visit_date.weekday() >= 6:  # Skip Sundays
        continue
    for dsp in active_dsps:
        dsp_outlets = [a for a in assignments if a["dsp_id"] == dsp["id"]]
        if not dsp_outlets:
            continue
        daily_visits = random.randint(6, min(dsp["daily_target_visits"], len(dsp_outlets)))
        visited = random.sample(dsp_outlets, min(daily_visits, len(dsp_outlets)))
        for asn in visited:
            hour = random.randint(8, 17)
            duration = random.randint(10, 45)
            checkin = visit_date.replace(hour=hour, minute=random.randint(0, 59))
            checkout = checkin + timedelta(minutes=duration)
            visits.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"visit-{len(visits)}")),
                "dsp_id": dsp["id"],
                "outlet_id": asn["outlet_id"],
                "visit_date": visit_date.date().isoformat(),
                "check_in_time": checkin.isoformat(),
                "check_out_time": checkout.isoformat(),
                "outcome": random.choices(
                    ["successful", "follow_up_needed", "merchant_absent", "no_action_needed"],
                    weights=[50, 25, 15, 10]
                )[0],
                "notes": random.choice([
                    "Merchant interested in activating GCredit",
                    "Low cash-in volume this week, advised on promotions",
                    "Successfully activated Pay QR service",
                    "Needs promo materials and standee",
                    "Discussed upcoming Bills Payment promo",
                    "Owner requested training on GInsure",
                    "Competitor (Maya) outlet nearby, merchant considering switch",
                    "High footfall area, suggested extending operating hours",
                    "Reminded about monthly target incentives",
                    "Merchant absent - will revisit tomorrow",
                    "Machine issue reported, escalated to tech support",
                    ""
                ])
            })

# ============================================================
# Action Recommendations
# ============================================================
ACTION_TYPES = ["visit_merchant", "upsell_product", "resolve_issue", "training", "reactivation", "follow_up"]
actions = []
for i in range(500):
    outlet = random.choice(outlets)
    dsp_matches = [a for a in assignments if a["outlet_id"] == outlet["id"]]
    dsp_id = dsp_matches[0]["dsp_id"] if dsp_matches else dsps[0]["id"]
    actions.append({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"action-{i}")),
        "outlet_id": outlet["id"],
        "dsp_id": dsp_id,
        "action_type": random.choice(ACTION_TYPES),
        "description": random.choice([
            "Activate GCredit for this merchant to increase transaction volume",
            "Follow up on pending Bills Payment activation",
            "Conduct training on new GInsure products",
            "Re-engage merchant - no transactions in 14 days",
            "Upsell Buy Load service - high foot traffic area",
            "Resolve merchant complaint about delayed settlements",
            "Offer promotional rates for Cash-In to combat Maya competition",
            "Schedule GSave onboarding session with merchant",
            "Investigate declining transaction volume trend",
            "Provide updated marketing collateral and QR standee",
        ]),
        "priority": random.choices(["high", "medium", "low"], weights=[30, 50, 20])[0],
        "status": random.choices(["pending", "in_progress", "completed", "skipped"], weights=[40, 20, 30, 10])[0],
        "due_date": (GEN_DATE + timedelta(days=random.randint(1, 30))).isoformat(),
        "created_at": (GEN_DATE - timedelta(days=random.randint(0, 14))).isoformat()
    })

# ============================================================
# Outlet Products
# ============================================================
outlet_products = []
for i, outlet in enumerate(outlets):
    # Cash-In and Cash-Out almost always active
    core = PRODUCTS[:2]
    others = random.sample(PRODUCTS[2:], k=random.randint(1, 6))
    activated = core + others
    for prod in activated:
        outlet_products.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"op-{i}-{prod['id']}")),
            "outlet_id": outlet["id"],
            "product_id": prod["id"],
            "status": random.choices(["active", "inactive", "pending"], weights=[80, 12, 8])[0],
            "activated_date": fake.date_between(start_date="-1y", end_date="-1m").isoformat()
        })

# ============================================================
# User Accounts
# ============================================================
users = []
for dsp in dsps:
    users.append({"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user-dsp-{dsp['id']}")), "email": dsp["email"], "password_hash": hashlib.sha256(b"password").hexdigest(), "role": "dsp", "dsp_id": dsp["id"], "is_active": True})
for mgr in managers:
    users.append({"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user-mgr-{mgr['id']}")), "email": mgr["email"], "password_hash": hashlib.sha256(b"password").hexdigest(), "role": "manager", "dsp_id": "", "is_active": True})
users.append({"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "admin")), "email": "admin@gcash.com", "password_hash": hashlib.sha256(b"password").hexdigest(), "role": "admin", "dsp_id": "", "is_active": True})

# ============================================================
# Write CSVs
# ============================================================
def write_csv(filename, data):
    if not data:
        return
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"  OK {filename:30s} -> {len(data):>6,} rows")

print(f"\nGenerating GCash-realistic CSV dataset to: {OUTPUT_DIR}\n")
write_csv("areas.csv", AREAS)
write_csv("products.csv", PRODUCTS)
write_csv("managers.csv", managers)
write_csv("dsps.csv", dsps)
write_csv("merchants.csv", merchants)
write_csv("outlets.csv", outlets)
write_csv("assignments.csv", assignments)
write_csv("outlet_scores.csv", scores)
write_csv("transactions.csv", transactions)
write_csv("visit_logs.csv", visits)
write_csv("action_recommendations.csv", actions)
write_csv("outlet_products.csv", outlet_products)
write_csv("users.csv", users)

# Print stats
print(f"\n--- Verification ---")
print(f"Cities: {', '.join(sorted(set(o['city'] for o in outlets))[:10])}...")
print(f"Txn types: { {t: sum(1 for x in transactions if x['txn_type']==t) for t in TXN_CONFIG} }")
load_txns = [float(t['amount']) for t in transactions if t['txn_type']=='buy_load']
print(f"Buy Load range: PHP {min(load_txns):.0f} - {max(load_txns):.0f} (avg PHP {sum(load_txns)/len(load_txns):.0f})")
qr_txns = [float(t['amount']) for t in transactions if t['txn_type']=='pay_qr']
print(f"Pay QR range: PHP {min(qr_txns):.0f} - {max(qr_txns):.0f} (avg PHP {sum(qr_txns)/len(qr_txns):.0f})")
all_amts = [float(t['amount']) for t in transactions]
print(f"Overall avg txn: PHP {sum(all_amts)/len(all_amts):,.0f}")
print(f"Visits: {len(visits)} total, {len(visits)/len(active_dsps)/52:.1f} per DSP/day")
print(f"\nDone! {len(list(OUTPUT_DIR.glob('*.csv')))} CSV files generated")
