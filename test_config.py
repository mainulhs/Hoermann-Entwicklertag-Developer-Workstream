"""
Property-based tests for Configuration Manager
Tests configuration parsing, validation, and error handling
"""

import pytest
import json
import yaml
import os
import tempfile
from hypothesis import given, strategies as st, settings, assume
from config import Config, ConfigurationError


# Strategies for generating test data

@st.composite
def valid_config_dict(draw):
    """Generate a valid configuration dictionary with all required settings"""
    return {
        'database': {
            'path': draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'), 
                whitelist_characters='._-/'
            )))
        },
        'server': {
            'host': draw(st.sampled_from(['localhost', '0.0.0.0', '127.0.0.1'])),
            'port': draw(st.integers(min_value=1024, max_value=65535)),
            'debug': draw(st.booleans())
        },
        'thresholds': {
            draw(st.text(min_size=1, max_size=20)): {
                'min': draw(st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False)),
                'max': draw(st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False)),
                'unit': draw(st.text(min_size=1, max_size=20))
            }
        }
    }


@st.composite
def invalid_config_dict(draw):
    """Generate an invalid configuration dictionary missing required settings"""
    # Randomly omit one or more required settings
    config = {}
    
    include_database = draw(st.booleans())
    include_server = draw(st.booleans())
    include_thresholds = draw(st.booleans())
    
    # Ensure at least one is missing
    assume(not (include_database and include_server and include_thresholds))
    
    if include_database:
        config['database'] = {'path': draw(st.text(min_size=1, max_size=50))}
    
    if include_server:
        config['server'] = {
            'host': 'localhost',
            'port': draw(st.integers(min_value=1024, max_value=65535))
        }
    
    if include_thresholds:
        config['thresholds'] = {}
    
    return config


# Property 33: Valid configuration parsing
# Feature: industrial-monitoring-system, Property 33: Valid configuration parsing
@given(config_data=valid_config_dict(), file_format=st.sampled_from(['json', 'yaml']))
@settings(max_examples=100, deadline=None)
@pytest.mark.property
def test_valid_configuration_parsing(config_data, file_format):
    """
    Property 33: Valid configuration parsing
    For any valid configuration file (JSON or YAML), 
    the system should successfully parse and load the configuration
    
    Validates: Requirements 9.1
    """
    # Create temporary config file
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=f'.{file_format}', 
        delete=False
    ) as f:
        if file_format == 'json':
            json.dump(config_data, f)
        else:  # yaml
            yaml.dump(config_data, f)
        temp_file = f.name
    
    try:
        # Parse configuration
        config = Config(temp_file)
        
        # Verify configuration was loaded successfully
        assert config is not None
        assert config.get('database') is not None
        assert config.get('server') is not None
        assert config.get('thresholds') is not None
        
        # Verify we can retrieve the data
        assert config.get('database.path') == config_data['database']['path']
        assert config.get('server.host') == config_data['server']['host']
        assert config.get('server.port') == config_data['server']['port']
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


# Property 34: Required settings validation
# Feature: industrial-monitoring-system, Property 34: Required settings validation
@given(config_data=invalid_config_dict(), file_format=st.sampled_from(['json', 'yaml']))
@settings(max_examples=100, deadline=None)
@pytest.mark.property
def test_required_settings_validation(config_data, file_format):
    """
    Property 34: Required settings validation
    For any configuration file missing required settings, 
    the system should fail to start and report which settings are missing
    
    Validates: Requirements 9.2
    """
    # Create temporary config file with missing settings
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=f'.{file_format}', 
        delete=False
    ) as f:
        if file_format == 'json':
            json.dump(config_data, f)
        else:  # yaml
            yaml.dump(config_data, f)
        temp_file = f.name
    
    try:
        # Attempt to parse configuration - should raise ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            Config(temp_file)
        
        # Verify error message mentions missing settings
        error_message = str(exc_info.value).lower()
        assert 'missing' in error_message or 'required' in error_message
        
        # Verify at least one required setting is mentioned in error
        required_settings = ['database', 'server', 'thresholds']
        missing_settings = [s for s in required_settings if s not in config_data]
        
        # At least one missing setting should be mentioned in the error
        assert any(setting in error_message for setting in missing_settings)
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


# Property 35: Invalid configuration error handling
# Feature: industrial-monitoring-system, Property 35: Invalid configuration error handling
@given(
    invalid_content=st.one_of(
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip() not in ['{}', '[]', '']),
        st.just('{invalid json content}'),
        st.just('invalid: yaml: content: [unclosed'),
    ),
    file_format=st.sampled_from(['json', 'yaml'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.property
def test_invalid_configuration_error_handling(invalid_content, file_format):
    """
    Property 35: Invalid configuration error handling
    For any invalid configuration file, 
    the system should fail to start with a descriptive error message
    
    Validates: Requirements 9.3
    """
    # Create temporary config file with invalid content
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=f'.{file_format}', 
        delete=False
    ) as f:
        f.write(invalid_content)
        temp_file = f.name
    
    try:
        # Attempt to parse configuration - should raise ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            Config(temp_file)
        
        # Verify error message is descriptive
        error_message = str(exc_info.value).lower()
        assert len(error_message) > 0
        
        # Error should mention either parsing issue, missing settings, or configuration issue
        assert any(keyword in error_message for keyword in [
            'invalid', 'error', 'missing', 'parse', 'json', 'yaml', 'configuration', 'dictionary', 'object'
        ])
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


# Additional unit tests for specific scenarios

@pytest.mark.unit
def test_nonexistent_config_file():
    """Test that Config raises error for nonexistent file"""
    with pytest.raises(ConfigurationError) as exc_info:
        Config('nonexistent_file.json')
    
    assert 'not found' in str(exc_info.value).lower()


@pytest.mark.unit
def test_unsupported_file_format():
    """Test that Config raises error for unsupported file format"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('some content')
        temp_file = f.name
    
    try:
        with pytest.raises(ConfigurationError) as exc_info:
            Config(temp_file)
        
        assert 'unsupported' in str(exc_info.value).lower()
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@pytest.mark.unit
def test_get_with_nested_keys():
    """Test that get() supports nested key access with dot notation"""
    config_data = {
        'database': {'path': 'test.db'},
        'server': {'host': 'localhost', 'port': 5000},
        'thresholds': {}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_file = f.name
    
    try:
        config = Config(temp_file)
        
        # Test nested key access
        assert config.get('database.path') == 'test.db'
        assert config.get('server.host') == 'localhost'
        assert config.get('server.port') == 5000
        
        # Test default value for missing key
        assert config.get('missing.key', 'default') == 'default'
        
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@pytest.mark.unit
def test_get_database_url():
    """Test get_database_url() method"""
    config_data = {
        'database': {'path': 'my_database.db'},
        'server': {'host': 'localhost', 'port': 5000},
        'thresholds': {}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_file = f.name
    
    try:
        config = Config(temp_file)
        assert config.get_database_url() == 'my_database.db'
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@pytest.mark.unit
def test_hardcoded_secrets():
    """Test that hardcoded secrets are present (intentional security flaw)"""
    config_data = {
        'database': {'path': 'test.db'},
        'server': {'host': 'localhost', 'port': 5000},
        'thresholds': {}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_file = f.name
    
    try:
        config = Config(temp_file)
        
        # Verify hardcoded secrets exist (this is intentional for workshop)
        assert config.get_secret_key() == "hardcoded-secret-key-12345"
        assert config.get_api_key() == "sk_live_abc123xyz789"
        
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
