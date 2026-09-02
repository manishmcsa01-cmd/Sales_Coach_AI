import random
from datetime import datetime
from .base import BaseGenerator

class ProductGenerator(BaseGenerator):
    PRODUCTS = [
        "GCash Cash-In", "Cash-Out", "Bills Payment", "Buy Load", "Send Money", 
        "Pay QR", "GInsure", "GInvest", "GCredit", "GSave", "GForest", 
        "GCash Mastercard", "QR Code Payments", "Bank Transfer", 
        "International Remittance", "Merchant Payments", "Mobile Top-up", 
        "Government Payments", "School Payments", "Healthcare Payments"
    ]

    def generate_products(self):
        return [{"id": self.generate_uuid(), "name": name} for name in self.PRODUCTS]

    def generate_outlet_products(self, outlets, products, count=5000):
        outlet_products = []
        for _ in range(count):
            outlet_products.append({
                "id": self.generate_uuid(),
                "outlet_id": random.choice(outlets)["id"],
                "product_id": random.choice(products)["id"],
                "activated_at": datetime.now()
            })
        return outlet_products
