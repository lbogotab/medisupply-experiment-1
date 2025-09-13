from flask import Flask
from .config import Config
from .routes.items import bp as items_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # Blueprints
    app.register_blueprint(items_bp)
    return app