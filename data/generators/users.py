import random
from passlib.hash import bcrypt
from .base import BaseGenerator

class UserGenerator(BaseGenerator):
    def generate_users(self, count=60):
        # 5 managers + 50 DSPs + 5 admins
        users = []
        pwd_hash = bcrypt.hash("salescoach123")
        
        for i in range(count):
            role = "dsp"
            if i < 5:
                role = "manager"
            elif i >= 55:
                role = "admin"
                
            first_name = self.faker.first_name().lower()
            last_name = self.faker.last_name().lower()
            
            users.append({
                "id": self.generate_uuid(),
                "email": f"{first_name}.{last_name}@gcash.com",
                "password_hash": pwd_hash,
                "role": role
            })
            
        return users
