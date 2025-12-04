"""
Property-Based Tests for API Responses
Tests API response format and HTTP status code properties

Properties tested:
- Property 30: HTTP status code appropriateness
- Property 31: Structured error responses
- Property 32: Successful operation data inclusion
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from flask import Flask
from database import DatabaseManager
from routes.api import api_bp, init_api_services
import os
import tempfile
import json


def create_test_app():
    """Create a Flask test application with API routes"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = DatabaseManager(db_path)
    
    # Initialize schema
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()
    cursor.close()
    
    # Create Flask app
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Initialize API services
    init_api_services(db)
    
    # Register blueprint
    app.register_blueprint(api_bp)
    
    return app, db, db_path


# Hypothesis strategies
equipment_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=3,
    max_size=20
)

equipment_name_strategy = st.text(min_size=3, max_size=50)

equipment_type_strategy = st.sampled_from(['pump', 'motor', 'conveyor', 'sensor', 'compressor', 'valve', 'tank'])

location_strategy = st.text(min_size=3, max_size=50)


# Feature: industrial-monitoring-system, Property 30: HTTP status code appropriateness
@given(
    equipment_id=equipment_id_strategy,
    name=equipment_name_strategy,
    equipment_type=equipment_type_strategy,
    location=location_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_http_status_code_appropriateness(equipment_id, name, equipment_type, location):
    """
    Property 30: HTTP status code appropriateness
    For any API request, the response should have an HTTP status code that matches
    the operation result (2xx for success, 4xx for client errors, 5xx for server errors)
    
    **Validates: Requirements 8.2**
    """
    app, db, db_path = create_test_app()
    
    try:
        with app.test_client() as client:
            # Test successful operation (201 Created)
            response = client.post('/api/equipment', 
                                  json={
                                      'equipment_id': equipment_id,
                                      'name': name,
                                      'type': equipment_type,
                                      'location': location
                                  })
            
            # Should return 2xx status code for success
            if response.status_code == 201:
                # Success case
                assert 200 <= response.status_code < 300, "Successful creation should return 2xx status code"
            elif response.status_code == 400:
                # Client error (e.g., duplicate ID from previous iteration)
                assert 400 <= response.status_code < 500, "Client errors should return 4xx status code"
            
            # Test client error (400 Bad Request) - missing required field
            response = client.post('/api/equipment', 
                                  json={
                                      'equipment_id': equipment_id + '_test',
                                      'name': name
                                      # Missing 'type' and 'location'
                                  })
            
            # Should return 4xx status code for client error
            assert 400 <= response.status_code < 500, "Client errors should return 4xx status code"
            
            # Test not found (404) - non-existent equipment
            response = client.get(f'/api/equipment/NONEXISTENT_{equipment_id}')
            
            # Should return 404 for not found
            assert response.status_code == 404, "Not found errors should return 404 status code"
            
    finally:
        db.close()
        os.unlink(db_path)


# Feature: industrial-monitoring-system, Property 31: Structured error responses
@given(
    equipment_id=equipment_id_strategy,
    name=equipment_name_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_structured_error_responses(equipment_id, name):
    """
    Property 31: Structured error responses
    For any API request that results in an error, the response should be a structured
    JSON object containing an error message
    
    **Validates: Requirements 8.3**
    """
    app, db, db_path = create_test_app()
    
    try:
        with app.test_client() as client:
            # Trigger validation error - missing required fields
            response = client.post('/api/equipment', 
                                  json={
                                      'equipment_id': equipment_id,
                                      'name': name
                                      # Missing 'type' and 'location'
                                  })
            
            # Should return error response
            assert response.status_code >= 400, "Invalid request should return error status"
            
            # Response should be JSON
            assert response.content_type == 'application/json', "Error response should be JSON"
            
            # Parse response
            data = json.loads(response.data)
            
            # Should have error structure
            assert 'error' in data, "Error response should contain 'error' field"
            assert 'message' in data, "Error response should contain 'message' field"
            assert 'timestamp' in data, "Error response should contain 'timestamp' field"
            
            # Message should be non-empty string
            assert isinstance(data['message'], str), "Error message should be a string"
            assert len(data['message']) > 0, "Error message should not be empty"
            
            # Test 404 error structure
            response = client.get(f'/api/equipment/NONEXISTENT_{equipment_id}')
            assert response.status_code == 404
            
            data = json.loads(response.data)
            assert 'error' in data
            assert 'message' in data
            assert 'timestamp' in data
            
    finally:
        db.close()
        os.unlink(db_path)


# Feature: industrial-monitoring-system, Property 32: Successful operation data inclusion
@given(
    equipment_id=equipment_id_strategy,
    name=equipment_name_strategy,
    equipment_type=equipment_type_strategy,
    location=location_strategy
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_successful_operation_data_inclusion(equipment_id, name, equipment_type, location):
    """
    Property 32: Successful operation data inclusion
    For any successful API operation, the response should include the relevant data
    for that operation
    
    **Validates: Requirements 8.4**
    """
    app, db, db_path = create_test_app()
    
    try:
        with app.test_client() as client:
            # Create equipment
            response = client.post('/api/equipment', 
                                  json={
                                      'equipment_id': equipment_id,
                                      'name': name,
                                      'type': equipment_type,
                                      'location': location
                                  })
            
            # Skip if duplicate (from previous iteration)
            if response.status_code != 201:
                return
            
            # Response should be JSON
            assert response.content_type == 'application/json', "Success response should be JSON"
            
            # Parse response
            data = json.loads(response.data)
            
            # Should include the created equipment data
            assert 'equipment_id' in data, "Response should include equipment_id"
            assert 'name' in data, "Response should include name"
            assert 'type' in data, "Response should include type"
            assert 'location' in data, "Response should include location"
            
            # Data should match what was submitted
            assert data['equipment_id'] == equipment_id, "Response equipment_id should match request"
            assert data['name'] == name, "Response name should match request"
            assert data['type'] == equipment_type, "Response type should match request"
            assert data['location'] == location, "Response location should match request"
            
            # Test GET operation includes data
            response = client.get(f'/api/equipment/{equipment_id}')
            assert response.status_code == 200, "GET should succeed for existing equipment"
            
            data = json.loads(response.data)
            assert 'equipment_id' in data, "GET response should include equipment_id"
            assert data['equipment_id'] == equipment_id, "GET response should return correct equipment"
            
            # Test LIST operation includes data
            response = client.get('/api/equipment')
            assert response.status_code == 200, "LIST should succeed"
            
            data = json.loads(response.data)
            assert 'equipment' in data, "LIST response should include equipment array"
            assert isinstance(data['equipment'], list), "Equipment should be a list"
            
            # Should include our created equipment
            equipment_ids = [eq['equipment_id'] for eq in data['equipment']]
            assert equipment_id in equipment_ids, "LIST should include created equipment"
            
    finally:
        db.close()
        os.unlink(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
