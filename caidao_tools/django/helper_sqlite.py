'''
Created on 2022年4月30日

@author: Administrator
'''
from django.db.backends.signals import connection_created
from django.apps import AppConfig

class SetWalConfig(AppConfig):

    def configure_sqlite(self, sender, connection, **_):
        if connection.vendor == 'sqlite':
            cursor = connection.cursor()
            cursor.execute('PRAGMA journal_mode=WAL;')
            cursor.execute('PRAGMA busy_timeout=5000;')    
    
    def ready(self):
        connection_created.connect(self.configure_sqlite)



