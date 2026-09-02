import random
from .base import BaseGenerator

class ActionGenerator(BaseGenerator):
    TYPES = ["re_engage", "upsell_product", "compliance_check", "training_visit", "retention_offer", "follow_up"]
    STATUSES = ["completed", "pending", "in_progress", "skipped"]

    def generate_actions(self, dsp_assignments, count=10000):
        actions = []
        for _ in range(count):
            assignment = random.choice(dsp_assignments)
            status = self.random_weighted_choice(self.STATUSES, [40, 30, 20, 10])
            notes = "Completed action successfully" if status == "completed" else ""
            actions.append({
                "id": self.generate_uuid(),
                "dsp_id": assignment["dsp_id"],
                "outlet_id": assignment["outlet_id"],
                "action_type": random.choice(self.TYPES),
                "status": status,
                "notes": notes
            })
        return actions
