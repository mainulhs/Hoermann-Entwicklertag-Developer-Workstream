"""
Routes package for Industrial Monitoring System
Exports API and Web UI blueprints
"""

from routes.api import api_bp, init_api_services
from routes.web import web_bp, init_web_services

__all__ = ['api_bp', 'web_bp', 'init_api_services', 'init_web_services']
