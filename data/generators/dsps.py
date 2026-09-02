import random
from .base import BaseGenerator

class DSPGenerator(BaseGenerator):
    AREA_NAMES = ["Metro Manila North", "Metro Manila South", "Metro Manila East", 
                  "Metro Manila West", "Cebu North", "Cebu South", "Davao North", 
                  "Davao South", "Pampanga", "Laguna"]

    def generate_areas(self, manager_ids):
        areas = []
        for i, name in enumerate(self.AREA_NAMES):
            manager_id = manager_ids[i // 2] if i // 2 < len(manager_ids) else manager_ids[0]
            areas.append({
                "id": self.generate_uuid(),
                "name": name,
                "manager_id": manager_id
            })
        return areas

    def generate_dsps(self, areas, user_ids):
        dsps = []
        for user_id in user_ids:
            area = random.choice(areas)
            dsps.append({
                "id": self.generate_uuid(),
                "user_id": user_id,
                "area_id": area["id"],
                "name": self.faker.name()
            })
        return dsps

    def assign_outlets(self, dsps, outlets):
        assignments = []
        outlet_pool = outlets.copy()
        random.shuffle(outlet_pool)
        
        for dsp in dsps:
            # 20 to 50 outlets per DSP
            num_outlets = random.randint(20, 50)
            assigned = [outlet_pool.pop() for _ in range(min(num_outlets, len(outlet_pool)))]
            for outlet in assigned:
                assignments.append({
                    "id": self.generate_uuid(),
                    "dsp_id": dsp["id"],
                    "outlet_id": outlet["id"],
                    "status": "active"
                })
        return assignments
