from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.locomotives import locomotives_bp
    from app.routes.loco_predictions import loco_predictions_bp
    from app.routes.reports import reports_bp
    from app.routes.data_collection import data_collection_bp
    from app.routes.user import user_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(locomotives_bp, url_prefix='/locomotives')
    app.register_blueprint(loco_predictions_bp, url_prefix='/loco-predictions')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(data_collection_bp, url_prefix='/data')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # Register template filters
    from app.filters import month_name, format_datetime, format_number, from_json
    app.jinja_env.filters['month_name'] = month_name
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['format_number'] = format_number
    app.jinja_env.filters['from_json'] = from_json
    
    return app
