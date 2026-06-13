import os
import threading
from flask import Flask
from flask_cors import CORS
from app.config import Config

tasks_lock = threading.Lock()
tasks = {}

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    CORS(app)
    
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
