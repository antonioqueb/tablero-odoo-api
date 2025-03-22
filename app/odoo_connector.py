import xmlrpc.client
from flask import current_app

class OdooConnector:
    def __init__(self):
        config = current_app.config
        self.url = config['ODOO_URL']
        self.db = config['ODOO_DB']
        self.username = config['ODOO_USER']
        self.password = config['ODOO_PASSWORD']

        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def is_connected(self):
        try:
            version = self.common.version()
            return True, version
        except Exception as e:
            return False, str(e)
