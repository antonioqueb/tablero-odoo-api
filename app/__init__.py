from flask import Flask
from .routes.health import health_bp
from .config import Config
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(health_bp, url_prefix="/health")

    return app
