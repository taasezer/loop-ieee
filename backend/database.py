from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

class Database:
    def __init__(self):
        mongo_url = os.environ['MONGO_URL']
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[os.environ.get('DB_NAME', 'loop_logistics')]
    
    @property
    def users(self):
        return self.db.users
    
    @property
    def couriers(self):
        return self.db.couriers
    
    @property
    def orders(self):
        return self.db.orders
    
    @property
    def locations(self):
        return self.db.locations
    
    @property
    def pricing_rules(self):
        return self.db.pricing_rules
    
    @property
    def earnings(self):
        return self.db.earnings
    
    @property
    def ratings(self):
        return self.db.ratings
    
    @property
    def notifications(self):
        return self.db.notifications
    
    @property
    def route_history(self):
        return self.db.route_history
    
    @property
    def payment_transactions(self):
        return self.db.payment_transactions
    
    @property
    def promotions(self):
        return self.db.promotions
    
    @property
    def system_config(self):
        return self.db.system_config

db = Database()
