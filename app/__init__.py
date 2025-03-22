from flask import Flask
from flask_cors import CORS  # ✅ Importar CORS
from .routes.health import health_bp
from .routes.ventas import ventas_bp
from .routes.compras import compras_bp
from .routes.manufactura import manufactura_bp

from .config import Config
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ✅ Habilitar CORS para todas las rutas y orígenes
    CORS(app)

    # ✅ Registrar los Blueprints
    app.register_blueprint(health_bp, url_prefix="/health")
    app.register_blueprint(ventas_bp, url_prefix="/ventas")
    app.register_blueprint(compras_bp, url_prefix="/compras")
    app.register_blueprint(manufactura_bp, url_prefix="/manufactura")


    return app
