import os

class Config:
    ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB = os.getenv("ODOO_DB", "nombre_de_base")
    ODOO_USERNAME = os.getenv("ODOO_USER", "admin")
    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
