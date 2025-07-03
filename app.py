import json
import random
from datetime import datetime, timedelta
from typing import Dict, List
import uuid

class EcommerceApp:
    def __init__(self):
        self.logs: List[Dict] = []
        self.users = self.generate_users(100)
        self.products = self.generate_products(50)
        self.current_time = datetime.now()

    def set_current_time(self, dt: datetime):
        """Définit l'heure simulée"""
        self.current_time = dt

    def log_event(self, event_type: str, data: Dict):
        """Prépare un log structuré en mémoire"""
        entry = {
            'timestamp': self.current_time.isoformat(),
            'event_type': event_type,
            'session_id': str(uuid.uuid4()),
            'user_id': data.get('user_id'),
            'ip_address': data.get('ip_address', self.generate_ip()),
            'user_agent': data.get('user_agent', self.generate_user_agent(data.get('device_type'))),
            'geo': data.get('geo'),
            'device_type': data.get('device_type'),
            'data': data.get('data', data)
        }
        self.logs.append(entry)

    def save_logs(self, filepath: str = 'app.json'):
        """Sauvegarde tous les logs dans un fichier JSON en tant que liste"""
        with open(filepath, 'w') as f:
            json.dump(self.logs, f, indent=2)

    def generate_users(self, n: int) -> List[Dict]:
        locations = [
            {'country':'FR','lat':48.8566,'lon':2.3522},
            {'country':'US','lat':37.7749,'lon':-122.4194},
            {'country':'JP','lat':35.6895,'lon':139.6917}
        ]
        devices = ['desktop','mobile','tablet']
        return [
            {
                'user_id': str(uuid.uuid4()),
                'geo': random.choice(locations),
                'device_type': random.choices(devices, weights=[0.5,0.4,0.1])[0]
            }
            for _ in range(n)
        ]

    def generate_products(self, n: int) -> List[Dict]:
        return [
            {'product_id': f'prod_{i}', 'name': f'Product {i}', 'price': round(random.uniform(10,500),2)}
            for i in range(1,n+1)
        ]

    def generate_ip(self) -> str:
        return '.'.join(str(random.randint(0,255)) for _ in range(4))

    def generate_user_agent(self, device: str=None) -> str:
        agents = {
            'desktop': ['Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64)'],
            'mobile': ['Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)', 'Mozilla/5.0 (Android 10)'],
            'tablet': ['Mozilla/5.0 (iPad; CPU OS 13_2 like Mac OS X)']
        }
        if device in agents:
            return random.choice(agents[device])
        return random.choice(sum(agents.values(), []))

    def time_based_actions(self) -> List[str]:
        h = self.current_time.hour
        if 6 <= h < 12:
            return ['search']*4 + ['page_view']*3 + ['product_view']
        if 12 <= h < 18:
            return ['page_view']*3 + ['product_view']*3 + ['add_to_cart']*2
        if 18 <= h < 22:
            return ['product_view']*2 + ['add_to_cart']*3 + ['purchase']*2
        return ['error']*2 + ['search'] + ['logout']

    # Méthodes d'événements
    def page_view(self, user):
        d = {'user_id':user['user_id'],'page':random.choice(['home','category','checkout'])}
        self.log_event('page_view', {'user_id':user['user_id'],'data':d,'geo':user['geo'],'device_type':user['device_type']})

    def product_view(self, user):
        p = random.choice(self.products)
        d = {'user_id':user['user_id'],'product_id':p['product_id'],'price':p['price']}
        self.log_event('product_view', {'user_id':user['user_id'],'data':d,'geo':user['geo'],'device_type':user['device_type']})

    def add_to_cart(self, user):
        p = random.choice(self.products)
        d = {'user_id':user['user_id'],'product_id':p['product_id'],'quantity':random.randint(1,5)}
        self.log_event('add_to_cart', {'user_id':user['user_id'],'data':d,'geo':user['geo'],'device_type':user['device_type']})

    def purchase(self, user):
        items=random.sample(self.products,k=random.randint(1,3))
        d={'user_id':user['user_id'],'order_id':str(uuid.uuid4()),
           'amount':round(sum(i['price'] for i in items),2),
           'items':[{'product_id':i['product_id'],'price':i['price']} for i in items]}
        self.log_event('purchase', {'user_id':user['user_id'],'data':d,'geo':user['geo'],'device_type':user['device_type']})

    def search(self, user):
        q = random.choice(['laptop','shoes','watch','phone','headphones'])
        d = {'user_id':user['user_id'],'query':q}
        self.log_event('search', {'user_id':user['user_id'],'data':d,'geo':user['geo'],'device_type':user['device_type']})

    def login(self, user):
        d = {'user_id':user['user_id']}
        self.log_event('login', {'user_id':user['user_id'],'data':d,'geo':user['geo'],'device_type':user['device_type']})

    def logout(self, user):
        d = {'user_id':user['user_id']}
        self.log_event('logout', {'user_id':user['user_id'],'data':d,'geo':user['geo'],'device_type':user['device_type']})

    def error(self, user):
        errs=[{'code':500,'msg':'Internal Server Error'},{'code':404,'msg':'Not Found'},{'code':403,'msg':'Forbidden'},{'code':502,'msg':'Bad Gateway'}]
        e=random.choice(errs)
        d={'user_id':user['user_id'],'error_code':e['code'],'error_message':e['msg']}
        self.log_event('error', {'user_id':user['user_id'],'data':d,'geo':user['geo'],'device_type':user['device_type']})

    def simulate_user_journey(self, load_factor: float=1.0, start_time: datetime=None):
        """Simule un parcours utilisateur avec temps contrôlé"""
        if start_time:
            self.set_current_time(start_time)
        user=random.choice(self.users)
        self.login(user)
        actions=self.time_based_actions()
        count=int(random.randint(5,15)*load_factor)
        for _ in range(count):
            act=random.choice(actions)
            try:
                getattr(self,act)(user)
            except Exception as e:
                self.log_event('error', {'user_id':user['user_id'],'data':{'error_code':0,'error_message':str(e)},'geo':user['geo'],'device_type':user['device_type']})
            advance = timedelta(seconds=random.uniform(30,120)/load_factor)
            self.current_time += advance
        self.logout(user)

if __name__ == '__main__':
    app = EcommerceApp()
    # Simulation sur 24h avec pics
    for hour in range(24):
        start = datetime.now().replace(hour=hour,minute=0,second=0,microsecond=0)
        load = 2.0 if 18 <= hour < 20 else 0.5 if hour < 6 else 1.0
        for _ in range(5):
            app.simulate_user_journey(load_factor=load, start_time=start)
    app.save_logs('app.json')
