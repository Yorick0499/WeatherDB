import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from pymongo import MongoClient


class Weather_App:
    def __init__(self):
        self.station = str(input('Podaj nazwę miejscowości: '))
        self.station_denormalize = self.station
        self.available = 0
        self.update = 0
        self.cache_exists = 0
    
    def get_data(self):
        file = open(f'cache/weather_{self.station}.json')
        data = json.load(file)
        print(f'Stacja: {data['stacja']}\nData pomiaru: {data['data_pomiaru']}\nGodzina pomiaru: {data['godzina_pomiaru']}:00\nTemperatura: {data['temperatura']}°C')
        file.close()

    def text_normalize(self):
        os.system('clear')
        polish_letters = {'ą':'a',
                        'ć':'c',
                        'ę':'e',
                        'ł':'l',
                        'ń':'n',
                        'ó':'o',
                        'ś':'s',
                        'ź':'z',
                        'ż':'z'}
        tab = []
        self.station = self.station.lower()
        for i in self.station:
            if i in polish_letters:
                i = polish_letters.get(i)
                tab.append(i)
            else:
                tab.append(i)
        self.station = ''.join(tab)
        self.station = self.station.replace('-', '')
        self.station = self.station.replace(' ', '')
    def check_config(self):
        config = open('config.json')
        data = json.load(config)
        if self.station in data['station']:
            self.available = 1
        config.close()
    
    def save_data(self):
        url = f'https://danepubliczne.imgw.pl/api/data/synop/station/{self.station}/format/json'
        print('Aktualizowanie danych pogodowych...')
        time.sleep(5)
        os.system('clear')
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            with open(f'cache/weather_{self.station}.json','w') as file:
                json.dump(data, file)
        else:
                print('No internet connection.')

    def update_data(self):
        y = datetime.now().year
        m = datetime.now().month
        d = datetime.now().day
        ymd = f'{y}-{m}-{d}'
        current_date = datetime.strptime(ymd, '%Y-%m-%d')
        file = open(f'cache/weather_{self.station}.json')
        data = json.load(file)
        if datetime.strptime(data['data_pomiaru'], '%Y-%m-%d') < current_date:
            self.update = 1
        elif datetime.strptime(data['data_pomiaru'], '%Y-%m-%d') == current_date and int(data['godzina_pomiaru'])+1 <  datetime.now().hour:
            self.update = 1
        else:
            self.update = 0
        file.close()

    def check_cache(self):
        path = Path(f'cache/weather_{self.station}.json')
        if path.exists():
            self.cache_exists = 1

    def get_cache(self):
        if self.update == 0:
            file = open(f'cache/weather_{self.station}.json')
            data = json.load(file)
            print(f'Stacja: {data['stacja']}\nData pomiaru: {data['data_pomiaru']}\nGodzina pomiaru: {data['godzina_pomiaru']}:00\nTemperatura: {data['temperatura']}°C')
            file.close()

    def check_db_cache(self):
        y = datetime.now().year
        m = datetime.now().month
        d = datetime.now().day
        h = datetime.now().hour
        if m < 10:
            ymd = f'{y}-0{m}-{d}'
        else:
            ymd = f'{y}-{m}-{d}'
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client['weather']
        collection = db['cache']
        if h == 0:
            mod_time = str(datetime.now().date() - timedelta(days=1))
            find_doc = collection.count_documents({'stacja':self.station_denormalize, 'data_pomiaru':mod_time, 'godzina_pomiaru':str((h-1)%24)})
        else:
            find_doc = collection.count_documents({'stacja':self.station_denormalize, 'data_pomiaru':ymd, 'godzina_pomiaru':str((h-1)%24)})
        if find_doc > 0:
            document = collection.find({'stacja':self.station_denormalize}, {'_id': 0,'id_stacji': 0, 'data_pomiaru': 0, 'godzina_pomiaru': 0, 'kierunek_wiatru': 0}).sort('_id', -1).limit(1)
            for i in document:
                for k,v in i.items():
                    k = k.replace('_', ' ')
                    if k == 'temperatura':
                        v = v + '℃'
                    print(f'{k.capitalize()}: {v}')
        else:
            url = f'https://danepubliczne.imgw.pl/api/data/synop/station/{self.station}/format/json'
            print('Aktualizowanie danych pogodowych...')
            time.sleep(5)
            os.system('clear')
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                collection.insert_one(data)
                document = collection.find({}, {'_id': 0,'id_stacji': 0, 'data_pomiaru': 0, 'godzina_pomiaru': 0, 'kierunek_wiatru': 0}).sort('_id', -1).limit(1)
                for i in document:
                    for k,v in i.items():
                        k = k.replace('_', ' ')
                        if k == 'temperatura':
                            v = v + '℃'
                        print(f'{k.capitalize()}: {v}')
            else:
                    print('No internet connection.')


    def run_app(self):
        self.text_normalize()
        self.check_config()
        self.check_cache()
        if self.available == 1:
            if self.cache_exists == 1:
                self.update_data()
                if self.update == 1:
                    self.save_data()
                    self.get_data()
                else:
                    self.get_cache()
            else:
                self.save_data()
                self.get_data()
        else:
            print('Station is unavailable.')
    
    def run_test_app(self):
        self.text_normalize()
        self.check_config()
        self.check_db_cache()

    

run = True
while run == True:
    test = Weather_App()
    test.run_test_app()
    print('\n1. Wróć\n2. Zakończ')
    user_input = int(input(': '))
    os.system('clear')
    if user_input == 1:
        run = True
    else:
        run = False


