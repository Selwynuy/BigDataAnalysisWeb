from flask import Flask, session
from flask_session import Session  # Add this import
import os


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SESSION_TYPE'] = 'filesystem'

    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize session
    Session(app)

    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)

    return app
