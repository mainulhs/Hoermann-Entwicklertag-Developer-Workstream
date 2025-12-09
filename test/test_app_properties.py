"""
Property-based tests for Application Entry Point
Tests that the application correctly uses configuration settings
"""

import pytest
import json
import os
import tempfile
import sqlite3
from hypothesis import given, strategies as st, settings
from config import Config
from database import DatabaseManager
from app import create_app


# Strategies for generating test data

@st.composite
def valid_database_config(draw):
    """Generate a valid configuration with database settings"""
    # Generate a unique database path for each test
    db_name = draw(st.text(
        min_size=5, 
        max_size=30,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-')
    ))
    
    return {
        'database': {
            'path': f'test_{db_name}.db'
        },
        'server': {
            'host': draw(st.sampled_from(['localhost', '127.0.0.1', '0.0.0.0'])),
            'port': draw(st.integers(min_value=5000, max_value=6000)),
            'debug': draw(st.booleans())
        },
        'thresholds': {
            'temperature': {
                'min': draw(st.floats(min_value=-50, max_value=0, allow_nan=False, allow_infinity=False)),
                'max': draw(st.floats(min_value=50, max_value=200, allow_nan=False, allow_infinity=False)),
                'unit': 'celsius'
            },
            'pressure': {
                'min': 0,
                'max': draw(st.floats(min_value=100, max_value=300, allow_nan=False, allow_infinity=False)),
                'unit': 'psi'
            }
        }
    }


# Property 36: Database configuration usage
# Feature: industrial-monitoring-system, Property 36: Database configuration usage
@given(config_data=valid_database_config())
@settings(max_examples=100, deadline=None)
@pytest.mark.property
def test_database_configuration_usage(config_data):
    """
    Property 36: Database configuration usage
    For any valid database configuration settings, 
    the system should establish database connections using those exact settings
    
    Validates: Requirements 9.4
    """
    # Create temporary config file
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.json', 
        delete=False
    ) as f:
        json.dump(config_data, f)
        temp_config_file = f.name
    
    db_path = config_data['database']['path']
    
    try:
        # Create Flask application with the configuration
        app = create_app(temp_config_file)
        
        # Verify that the application uses the exact database path from configuration
        assert app.config['DATABASE_PATH'] == db_path
        
        # Verify that the database manager is using the correct path
        assert app.db_manager.db_path == db_path
        
        # Verify that the database file was created at the specified path
        assert os.path.exists(db_path)
        
        # Verify we can connect to the database at the configured path
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verify schema was initialized (check for expected tables)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Should have the core tables from schema
        expected_tables = ['equipment', 'sensor_readings', 'alerts', 'maintenance', 'users']
        for table in expected_tables:
            assert table in tables, f"Expected table '{table}' not found in database"
        
        conn.close()
        
        # Verify server configuration was also loaded correctly
        assert app.config['HOST'] == config_data['server']['host']
        assert app.config['PORT'] == config_data['server']['port']
        assert app.config['DEBUG'] == config_data['server']['debug']
        
        # Verify threshold configuration was loaded
        assert app.config['THRESHOLDS'] == config_data['thresholds']
        
    finally:
        # Clean up temporary files
        if os.path.exists(temp_config_file):
            os.unlink(temp_config_file)
        
        if os.path.exists(db_path):
            os.unlink(db_path)


# Additional unit tests for app initialization

@pytest.mark.unit
def test_app_initialization_with_default_config():
    """Test that app initializes correctly with default config.json"""
    # This test assumes config.json exists in the project root
    if not os.path.exists('config.json'):
        pytest.skip("config.json not found")
    
    app = create_app('config.json')
    
    # Verify app was created
    assert app is not None
    
    # Verify database manager was initialized
    assert hasattr(app, 'db_manager')
    assert app.db_manager is not None
    
    # Verify blueprints were registered
    assert 'api' in app.blueprints
    assert 'web' in app.blueprints


@pytest.mark.unit
def test_app_initialization_with_missing_config():
    """Test that app fails gracefully with missing config file"""
    import sys
    from io import StringIO
    
    # Capture stderr
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    
    try:
        # This should exit with error code 1
        with pytest.raises(SystemExit) as exc_info:
            create_app('nonexistent_config.json')
        
        assert exc_info.value.code == 1
        
        # Verify error message was printed
        error_output = sys.stderr.getvalue()
        assert 'Configuration error' in error_output or 'not found' in error_output
        
    finally:
        sys.stderr = old_stderr


@pytest.mark.unit
def test_app_uses_schema_file():
    """Test that app initializes database schema from schema.sql"""
    config_data = {
        'database': {'path': 'test_schema_init.db'},
        'server': {'host': 'localhost', 'port': 5000, 'debug': False},
        'thresholds': {'temperature': {'min': 0, 'max': 100, 'unit': 'celsius'}}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_file = f.name
    
    db_path = config_data['database']['path']
    
    try:
        # Create app - should initialize schema
        app = create_app(temp_config_file)
        
        # Verify schema was initialized by checking for tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Should have all expected tables
        assert 'equipment' in tables
        assert 'sensor_readings' in tables
        assert 'alerts' in tables
        assert 'maintenance' in tables
        assert 'users' in tables
        
    finally:
        if os.path.exists(temp_config_file):
            os.unlink(temp_config_file)
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.unit
def test_app_config_values_from_file():
    """Test that app correctly loads all configuration values"""
    config_data = {
        'database': {'path': 'test_config_values.db'},
        'server': {
            'host': '192.168.1.100',
            'port': 8080,
            'debug': True
        },
        'thresholds': {
            'temperature': {'min': -20, 'max': 150, 'unit': 'celsius'},
            'pressure': {'min': 10, 'max': 200, 'unit': 'bar'}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_config_file = f.name
    
    db_path = config_data['database']['path']
    
    try:
        app = create_app(temp_config_file)
        
        # Verify all configuration values were loaded correctly
        assert app.config['DATABASE_PATH'] == 'test_config_values.db'
        assert app.config['HOST'] == '192.168.1.100'
        assert app.config['PORT'] == 8080
        assert app.config['DEBUG'] is True
        
        # Verify thresholds
        assert app.config['THRESHOLDS']['temperature']['min'] == -20
        assert app.config['THRESHOLDS']['temperature']['max'] == 150
        assert app.config['THRESHOLDS']['pressure']['min'] == 10
        assert app.config['THRESHOLDS']['pressure']['max'] == 200
        
    finally:
        if os.path.exists(temp_config_file):
            os.unlink(temp_config_file)
        if os.path.exists(db_path):
            os.unlink(db_path)
