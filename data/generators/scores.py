import random
import json
from datetime import datetime
from .base import BaseGenerator

class ScoreGenerator(BaseGenerator):
    FACTORS = [
        "declining_txn_volume", "no_recent_visit", "product_upsell_opportunity", 
        "high_churn_risk", "dormancy_warning", "competitor_risk", 
        "seasonal_opportunity", "compliance_issue"
    ]

    def generate_scores(self, outlets, days=30):
        scores = []
        end_date = datetime.now()
        for outlet in outlets:
            for day_offset in range(days):
                score = random.uniform(10, 100)
                factors = random.sample(self.FACTORS, k=random.randint(1, 3))
                scores.append({
                    "id": self.generate_uuid(),
                    "outlet_id": outlet["id"],
                    "priority_score": round(score, 2),
                    "contributing_factors": json.dumps(factors),
                    "computed_at": end_date - timedelta(days=day_offset)
                })
        return scores
