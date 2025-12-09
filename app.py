"""
Industrial Equipment Monitoring System - Main Application Entry Point

This is a Flask-based web application for monitoring industrial equipment,
tracking sensor data, managing maintenance schedules, and providing alerting capabilities.

INTENTIONAL FLAWS FOR WORKSHOP TRAINING:
- Security vulnerabilities (SQL injection, hardcoded secrets, plain text passwords)
- Performance issues (N+1 queries, missing indexes, no pagination)
- Code quality issues (weak token generation, no input sanitization)

Usage:
    python app.py                    # Run with default config.json
    python app.py --config custom.json  # Run with custom config
    python app.py --generate-sample-data  # Populate database with sample data
"""

import argparse
import sys
from flask import Flask
from config import Config, ConfigurationError
from database import DatabaseManager
from routes.api import api_bp, init_api_services
from routes.web import web_bp, init_web_services
from utils.sample_data import SampleDataGenerator



def create_app(config_path: str = "config.json") -> Flask:
    """
    Create and configure Flask application
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured Flask application instance
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    try:
        config = Config(config_path)
        print(f"✓ Configuration loaded from {config_path}")
    except ConfigurationError as e:
        print(f"✗ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Set Flask configuration
    app.config['SECRET_KEY'] = config.get_secret_key()
    app.config['DATABASE_PATH'] = config.get_database_url()
    
    # Get server configuration
    server_config = config.get_server_config()
    app.config['HOST'] = server_config.get('host', '127.0.0.1')
    app.config['PORT'] = server_config.get('port', 5000)
    app.config['DEBUG'] = server_config.get('debug', False)
    
    # Store threshold configuration for services
    app.config['THRESHOLDS'] = config.get_threshold_config()
    
    # Initialize database
    db_manager = DatabaseManager(app.config['DATABASE_PATH'])
    
    # Initialize schema if database doesn't exist or is empty
    try:
        # Check if tables exist
        tables = db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        
        if not tables:
            print("Initializing database schema...")
            db_manager.init_schema()
            print("✓ Database schema initialized")
        else:
            print(f"✓ Database connected ({len(tables)} tables found)")
    except Exception as e:
        print(f"✗ Database initialization error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Store database manager in app context
    app.db_manager = db_manager
    

    
    # Initialize services for API routes
    init_api_services(db_manager)
    print("✓ API services initialized")
    
    # Initialize services for web UI routes
    init_web_services(db_manager)
    print("✓ Web UI services initialized")
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)
    print("✓ Routes registered")
    
    # Add translation function to template context
    from utils.i18n import _
    app.jinja_env.globals['_'] = _
    
    # Add language switching route
    @app.route('/set_language/<language>')
    def set_language(language):
        from flask import redirect, request, session
        if language in ['en', 'de']:
            session['language'] = language
        return redirect(request.referrer or '/')
    
    return app


def generate_sample_data(app: Flask):
    """
    Generate and populate database with sample data
    
    Args:
        app: Flask application instance with database manager
    """
    print("\nGenerating sample data...")
    
    try:
        generator = SampleDataGenerator(app.db_manager)
        generator.populate_database()
        print("✓ Sample data generated successfully")
    except Exception as e:
        print(f"✗ Error generating sample data: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main entry point for the application
    
    Parses command-line arguments and starts the Flask server
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Industrial Equipment Monitoring System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                           # Run with default config.json
  python app.py --config custom.json      # Run with custom configuration
  python app.py --generate-sample-data    # Populate database with sample data
  python app.py --host 0.0.0.0 --port 8080  # Run on custom host/port
        """
    )
    
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--generate-sample-data',
        action='store_true',
        help='Generate sample data and populate database'
    )
    
    parser.add_argument(
        '--host',
        help='Host to bind to (overrides config file)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        help='Port to bind to (overrides config file)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (overrides config file)'
    )
    
    args = parser.parse_args()
    
    # Create Flask application
    print("=" * 60)
    print("Industrial Equipment Monitoring System")
    print("=" * 60)
    
    app = create_app(args.config)
    
    # Generate sample data if requested
    if args.generate_sample_data:
        generate_sample_data(app)
        print("\nSample data generation complete.")
        print("You can now start the server to view the data.")
        return
    
    # Override configuration with command-line arguments
    if args.host:
        app.config['HOST'] = args.host
    if args.port:
        app.config['PORT'] = args.port
    if args.debug:
        app.config['DEBUG'] = True
    
    # Print startup information
    print("\n" + "=" * 60)
    print("Server Configuration:")
    print(f"  Host: {app.config['HOST']}")
    print(f"  Port: {app.config['PORT']}")
    print(f"  Debug: {app.config['DEBUG']}")
    print(f"  Database: {app.config['DATABASE_PATH']}")
    print("=" * 60)
    print("\nAPI Endpoints:")
    print(f"  http://{app.config['HOST']}:{app.config['PORT']}/api/equipment")
    print(f"  http://{app.config['HOST']}:{app.config['PORT']}/api/sensors/readings")
    print(f"  http://{app.config['HOST']}:{app.config['PORT']}/api/alerts")
    print(f"  http://{app.config['HOST']}:{app.config['PORT']}/api/maintenance")
    print(f"  http://{app.config['HOST']}:{app.config['PORT']}/api/auth/login")
    print("\nWeb Interface:")
    print(f"  http://{app.config['HOST']}:{app.config['PORT']}/")
    print("=" * 60)
    print("\nStarting server... (Press Ctrl+C to stop)")
    print()
    
    # Start Flask development server
    try:
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG']
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n✗ Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
