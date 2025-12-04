"""
Configuration Manager for Industrial Monitoring System
Handles loading and parsing configuration from JSON/YAML files
"""

import json
import yaml
import os
from typing import Any, Optional, Dict


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing required settings"""
    pass


class Config:
    """
    Configuration manager with intentional security flaws for workshop training
    
    SECURITY VULNERABILITIES (INTENTIONAL):
    - Hardcoded SECRET_KEY and API_KEY
    - These should be loaded from environment variables or secure vaults
    """
    
    # INTENTIONAL SECURITY FLAW: Hardcoded secrets
    SECRET_KEY = "hardcoded-secret-key-12345"
    API_KEY = "sk_live_abc123xyz789"
    
    # Required configuration keys that must be present
    REQUIRED_SETTINGS = [
        'database',
        'server',
        'thresholds'
    ]
    
    def __init__(self, config_file: str):
        """
        Initialize Config by loading configuration from file
        
        Args:
            config_file: Path to JSON or YAML configuration file
            
        Raises:
            ConfigurationError: If file doesn't exist, is invalid, or missing required settings
        """
        self.config_file = config_file
        self._config_data: Dict[str, Any] = {}
        self._load_config()
        self._validate_required_settings()
    
    def _load_config(self):
        """
        Load configuration from JSON or YAML file
        
        Raises:
            ConfigurationError: If file doesn't exist or cannot be parsed
        """
        if not os.path.exists(self.config_file):
            raise ConfigurationError(f"Configuration file not found: {self.config_file}")
        
        try:
            with open(self.config_file, 'r') as f:
                # Determine file type by extension
                if self.config_file.endswith('.json'):
                    self._config_data = json.load(f)
                elif self.config_file.endswith(('.yaml', '.yml')):
                    self._config_data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format. Use .json, .yaml, or .yml"
                    )
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")
    
    def _validate_required_settings(self):
        """
        Validate that all required settings are present in configuration
        
        Raises:
            ConfigurationError: If any required settings are missing
        """
        # Ensure config data is a dictionary
        if not isinstance(self._config_data, dict):
            raise ConfigurationError(
                f"Configuration must be a dictionary/object, got {type(self._config_data).__name__}"
            )
        
        missing_settings = []
        for setting in self.REQUIRED_SETTINGS:
            if setting not in self._config_data:
                missing_settings.append(setting)
        
        if missing_settings:
            raise ConfigurationError(
                f"Missing required configuration settings: {', '.join(missing_settings)}"
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key
        
        Args:
            key: Configuration key (supports nested keys with dot notation, e.g., 'database.path')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Support nested keys with dot notation
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_url(self) -> str:
        """
        Get database connection URL/path
        
        Returns:
            Database path from configuration
            
        Raises:
            ConfigurationError: If database configuration is missing
        """
        db_config = self.get('database')
        if not db_config:
            raise ConfigurationError("Database configuration is missing")
        
        # Support both 'path' and 'url' keys
        db_path = db_config.get('path') or db_config.get('url')
        if not db_path:
            raise ConfigurationError("Database path/url not specified in configuration")
        
        return db_path
    
    def get_secret_key(self) -> str:
        """
        Get secret key for session management
        
        INTENTIONAL SECURITY FLAW: Returns hardcoded secret key
        In production, this should load from environment variables or secure vault
        
        Returns:
            Secret key (hardcoded)
        """
        return self.SECRET_KEY
    
    def get_api_key(self) -> str:
        """
        Get API key for external service authentication
        
        INTENTIONAL SECURITY FLAW: Returns hardcoded API key
        In production, this should load from environment variables or secure vault
        
        Returns:
            API key (hardcoded)
        """
        return self.API_KEY
    
    def get_server_config(self) -> Dict[str, Any]:
        """
        Get server configuration (host, port, debug mode)
        
        Returns:
            Server configuration dictionary
        """
        return self.get('server', {})
    
    def get_threshold_config(self) -> Dict[str, Any]:
        """
        Get sensor threshold configuration
        
        Returns:
            Threshold configuration dictionary
        """
        return self.get('thresholds', {})
    
    def __repr__(self) -> str:
        """String representation of Config object"""
        return f"Config(file='{self.config_file}')"
