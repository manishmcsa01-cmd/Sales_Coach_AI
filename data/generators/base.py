import uuid
import random
from datetime import datetime, timedelta
from faker import Faker

class BaseGenerator:
    def __init__(self):
        self.faker = Faker(locale='en_PH')
        
    def generate_uuid(self):
        return str(uuid.uuid4())
        
    def random_date_in_range(self, start_date, end_date):
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        return start_date + timedelta(days=random_days)
        
    def random_weighted_choice(self, choices, weights):
        return random.choices(choices, weights=weights, k=1)[0]
