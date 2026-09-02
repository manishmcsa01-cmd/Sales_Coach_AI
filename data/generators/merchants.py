import random
from .base import BaseGenerator

class MerchantGenerator(BaseGenerator):
    MERCHANT_TYPES = ["sari_sari", "pharmacy", "convenience", "supermarket", "other"]
    KYC_STATUSES = ["pending", "verified", "rejected"]
    RISK_TIERS = ["low", "medium", "high"]
    CITIES = [
        ("Metro Manila", 14.5995, 120.9842),
        ("Cebu", 10.3157, 123.8854),
        ("Davao", 7.1907, 125.4553)
    ]

    def generate_merchants(self, count=500):
        merchants = []
        for _ in range(count):
            merchants.append({
                "id": self.generate_uuid(),
                "name": f"{self.faker.last_name()} {self.faker.company_suffix()}",
                "type": self.random_weighted_choice(self.MERCHANT_TYPES, [50, 15, 15, 10, 10]),
                "kyc_status": self.random_weighted_choice(self.KYC_STATUSES, [20, 70, 10]),
                "risk_tier": self.random_weighted_choice(self.RISK_TIERS, [60, 30, 10])
            })
        return merchants

    def generate_outlets(self, merchants, count=2000):
        outlets = []
        merchant_pool = merchants * 4 # Adjust distribution roughly
        for i in range(count):
            merchant = random.choice(merchants)
            city_name, lat, lng = random.choice(self.CITIES)
            
            # small offset for lat lng
            lat_offset = random.uniform(-0.05, 0.05)
            lng_offset = random.uniform(-0.05, 0.05)
            
            outlets.append({
                "id": self.generate_uuid(),
                "merchant_id": merchant["id"],
                "name": f"{merchant['name']} - {self.faker.street_name()}",
                "address": self.faker.address(),
                "city": city_name,
                "latitude": lat + lat_offset,
                "longitude": lng + lng_offset
            })
        return outlets
