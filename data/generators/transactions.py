import random
from datetime import datetime, timedelta
from .base import BaseGenerator

class TransactionGenerator(BaseGenerator):
    TYPES = ["cash_in", "cash_out", "bills_pay", "buy_load", "send_money", "pay_qr"]
    AMOUNTS = {
        "cash_in": (500, 10000),
        "cash_out": (500, 10000),
        "bills_pay": (200, 5000),
        "buy_load": (10, 1000),
        "send_money": (100, 5000),
        "pay_qr": (50, 3000)
    }

    def generate_transactions(self, outlets, count=200000, days=90):
        transactions = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 80/20 rule
        high_vol_outlets = random.sample(outlets, k=int(len(outlets) * 0.2))
        low_vol_outlets = [o for o in outlets if o not in high_vol_outlets]
        
        declining_outlets = set([o["id"] for o in random.sample(outlets, k=int(len(outlets) * 0.15))])
        churn_risk_outlets = set([o["id"] for o in random.sample(outlets, k=int(len(outlets) * 0.05))])

        for _ in range(count):
            is_high_vol = random.random() < 0.8
            outlet = random.choice(high_vol_outlets) if is_high_vol else random.choice(low_vol_outlets)
            
            txn_date = self.random_date_in_range(start_date, end_date)
            
            if outlet["id"] in churn_risk_outlets:
                if (end_date - txn_date).days < 14:
                    continue # Skip recent txns for churn risk
                    
            if outlet["id"] in declining_outlets:
                if (end_date - txn_date).days < 30:
                    if random.random() < 0.7:
                        continue # Suppress recent txns to simulate decline

            txn_type = random.choice(self.TYPES)
            min_amt, max_amt = self.AMOUNTS[txn_type]
            
            transactions.append({
                "id": self.generate_uuid(),
                "outlet_id": outlet["id"],
                "transaction_type": txn_type,
                "amount": round(random.uniform(min_amt, max_amt), 2),
                "timestamp": txn_date
            })
            
        return transactions
