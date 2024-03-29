import redis
from datetime import datetime

class RedisClient:
    def __init__(self):
        self.db = redis.Redis(host='localhost', port=6379, db=0)
        self.ts = self.db.ts()
        self.epoch = datetime.utcfromtimestamp(0)

    def add_dl_position_1(self, time, pos):
        unix_time = self.unix_time_ms(time)
        self.ts.add('dl_pos_1', unix_time, pos)
    
    def add_temperature_1(self, time, temp):
        unix_time = self.unix_time_ms(time)
        self.ts.add('dl_T1', unix_time, temp)

    def add_temperature_2(self, time, temp):
        unix_time = self.unix_time_ms(time)
        self.ts.add('dl_T2', unix_time, temp)

    def add_temperature_3(self, time, temp):
        unix_time = self.unix_time_ms(time)
        self.ts.add('dl_T3', unix_time, temp)

    def add_temperature_4(self, time, temp):
        unix_time = self.unix_time_ms(time)
        self.ts.add('dl_T4', unix_time, temp)

    def unix_time_ms(self, time):
        return round((time - self.epoch).total_seconds() * 1000.0)