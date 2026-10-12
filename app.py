import os
import logging
from flask import Flask, render_template, redirect, url_for, session, request
from config import Config
import db

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.village_routes import village_bp
from routes.import_routes import import_bp
from routes.kml_routes import kml_bp
from routes.export_routes import export_bp
from routes.settings_routes import settings_bp
from routes.automation_routes import automation_bp
from routes.person_routes import person_bp
from routes.user_routes import user_bp
from routes.user_work_routes import user_work_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory for Master Borewell & Tubewell Management Portal."""
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )
    app.config.from_object(Config)

    # Ensure upload folders exist
    Config.ensure_dirs()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(village_bp)
    app.register_blueprint(person_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(user_work_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(kml_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(automation_bp)


    # UI Page Routes
    @app.route('/login')
    def login_page():
        if 'user_id' in session:
            return redirect(url_for('index_page'))
        return render_template('login.html')

    @app.route('/')
    def index_page():
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('index.html', user={
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role')
        })

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith('/api/'):
            return {"success": False, "error": "Endpoint not found."}, 404
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return render_template('index.html', user={
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role')
        }), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {e}")
        return {"success": False, "error": "Internal server error occurred."}, 500

    # Initialize Database Schema if needed
    try:
        db.init_db()
    except Exception as e:
        logger.warning(f"Could not initialize DB on startup: {e}. Ensure SQL Server is reachable.")

    return app


app = create_app()

if __name__ == '__main__':
    logger.info(f"Starting server on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
