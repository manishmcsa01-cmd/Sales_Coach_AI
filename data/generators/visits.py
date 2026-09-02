import random
from datetime import datetime, timedelta
from .base import BaseGenerator

class VisitGenerator(BaseGenerator):
    OUTCOMES = ["successful", "follow_up_needed", "merchant_absent", "no_action_needed"]

    def generate_visits(self, dsp_assignments, count=15000, days=90):
        visits = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for _ in range(count):
            assignment = random.choice(dsp_assignments)
            visits.append({
                "id": self.generate_uuid(),
                "dsp_id": assignment["dsp_id"],
                "outlet_id": assignment["outlet_id"],
                "timestamp": self.random_date_in_range(start_date, end_date),
                "duration_minutes": random.randint(15, 60),
                "outcome": self.random_weighted_choice(self.OUTCOMES, [60, 20, 10, 10])
            })
            
        return visits
