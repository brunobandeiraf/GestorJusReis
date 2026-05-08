"""Flask application factory."""
import os

import click
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration to use ('development', 'testing', 'production').
                     Defaults to 'development' if not specified.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Load configuration
    if config_name is None:
        config_name = 'development'

    from app.config import config_by_name
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    _register_blueprints(app)

    # Register CLI commands
    _register_cli_commands(app)

    # Configure scheduler (only in non-testing mode)
    if not app.config.get('TESTING', False):
        from app.services.scheduler_service import configurar_scheduler
        configurar_scheduler(app)

    return app


def _register_blueprints(app):
    """Register Flask blueprints with the app."""
    from app.routes.processos import processos_bp
    app.register_blueprint(processos_bp)

    from app.routes.consulta import consulta_bp
    app.register_blueprint(consulta_bp)

    from app.routes.health import health_bp
    app.register_blueprint(health_bp)


def _register_cli_commands(app):
    """Register custom CLI commands with the Flask app."""

    @app.cli.command('init-db')
    @click.option('--drop', is_flag=True, help='Drop existing tables before creating.')
    def init_db_command(drop):
        """Initialize the database by creating all tables."""
        # Import models to ensure they are registered with SQLAlchemy
        from app import models  # noqa: F401

        if drop:
            db.drop_all()
            click.echo('Dropped all tables.')

        db.create_all()
        click.echo('Database initialized successfully.')
