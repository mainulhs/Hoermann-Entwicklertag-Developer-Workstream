"""
Property-based tests for sensor data operations
Tests Properties 5, 6, 7, and 8 from the design document
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
import tempfile
import os

from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository


# Strategy for generating valid equipment data
equipment_strategy = st.fixed_dictionaries({
    'equipment_id': st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
    )),
    'name': st.text(min_size=1, max_size=100),
    'type': st.sampled_from(['pump', 'motor', 'conveyor', 'sensor', 'compressor', 'valve']),
    'location': st.text(min_size=1, max_size=100)
})

# Strategy for generating valid sensor readings
sensor_reading_strategy = st.fixed_dictionaries({
    'sensor_type': st.sampled_from(['temperature', 'pressure', 'vibration', 'flow', 'speed']),
    'value': st.floats(min_value=-100.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    'unit': st.sampled_from(['C', 'F', 'PSI', 'bar', 'Hz', 'RPM', 'L/min'])
})


def create_test_db():
    """Create a temporary database for testing"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = DatabaseManager(db_path)
    db.init_schema('schema.sql')
    
    return db, db_path


def cleanup_test_db(db, db_path):
    """Clean up test database"""
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


# Feature: industrial-monitoring-system, Property 5: Sensor reading validation
@given(equipment=equipment_strategy, reading=sensor_reading_strategy)
@settings(max_examples=100)
def test_property_5_sensor_reading_validation(equipment, reading):
    """
    Property 5: Sensor reading validation
    For any sensor reading submission, if any required field 
    (equipment_id, sensor_type, value, timestamp) is missing, 
    the validation should reject the reading
    
    Validates: Requirements 2.1
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    sensor_repo = SensorDataRepository(db)
    
    try:
        # First create equipment
        equipment_repo.create(equipment)
        
        # Create complete sensor reading
        complete_reading = {
            'equipment_id': equipment['equipment_id'],
            'sensor_type': reading['sensor_type'],
            'value': reading['value'],
            'unit': reading['unit'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Test with all required fields present - should succeed
        result_id = sensor_repo.create(complete_reading)
        assert result_id > 0
        
        # Test with each required field missing - should fail
        required_fields = ['equipment_id', 'sensor_type', 'value']
        
        for field_to_remove in required_fields:
            incomplete_reading = complete_reading.copy()
            del incomplete_reading[field_to_remove]
            
            with pytest.raises(KeyError):
                sensor_repo.create(incomplete_reading)
    finally:
        cleanup_test_db(db, db_path)


# Feature: industrial-monitoring-system, Property 6: Sensor reading round-trip
@given(equipment=equipment_strategy, reading=sensor_reading_strategy)
@settings(max_examples=100)
def test_property_6_sensor_reading_roundtrip(equipment, reading):
    """
    Property 6: Sensor reading round-trip
    For any valid sensor reading, after storing it, 
    querying sensor readings should include a reading with equivalent data
    
    Validates: Requirements 2.2
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    sensor_repo = SensorDataRepository(db)
    
    try:
        # First create equipment
        equipment_repo.create(equipment)
        
        # Create sensor reading
        sensor_reading = {
            'equipment_id': equipment['equipment_id'],
            'sensor_type': reading['sensor_type'],
            'value': reading['value'],
            'unit': reading['unit'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Store reading
        result_id = sensor_repo.create(sensor_reading)
        assert result_id > 0
        
        # Query readings for this equipment
        retrieved_readings = sensor_repo.get_by_equipment(equipment['equipment_id'])
        
        # Verify reading is present with equivalent data
        assert len(retrieved_readings) > 0
        found = False
        for retrieved in retrieved_readings:
            if (retrieved['equipment_id'] == sensor_reading['equipment_id'] and
                retrieved['sensor_type'] == sensor_reading['sensor_type'] and
                abs(retrieved['value'] - sensor_reading['value']) < 0.001 and
                retrieved['unit'] == sensor_reading['unit']):
                found = True
                break
        assert found, "Sensor reading not found in query results"
    finally:
        cleanup_test_db(db, db_path)


# Feature: industrial-monitoring-system, Property 7: Sensor reading association
@given(equipment=equipment_strategy, reading=sensor_reading_strategy)
@settings(max_examples=100)
def test_property_7_sensor_reading_association(equipment, reading):
    """
    Property 7: Sensor reading association
    For any sensor reading stored with a valid equipment_id, 
    querying that equipment's sensor history should include the reading
    
    Validates: Requirements 2.3
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    sensor_repo = SensorDataRepository(db)
    
    try:
        # First create equipment
        equipment_repo.create(equipment)
        
        # Create sensor reading
        sensor_reading = {
            'equipment_id': equipment['equipment_id'],
            'sensor_type': reading['sensor_type'],
            'value': reading['value'],
            'unit': reading['unit'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Store reading
        result_id = sensor_repo.create(sensor_reading)
        assert result_id > 0
        
        # Query equipment's sensor history
        equipment_readings = sensor_repo.get_by_equipment(equipment['equipment_id'])
        
        # Verify reading is in the equipment's history
        assert len(equipment_readings) > 0
        equipment_ids = [r['equipment_id'] for r in equipment_readings]
        assert equipment['equipment_id'] in equipment_ids
    finally:
        cleanup_test_db(db, db_path)


# Feature: industrial-monitoring-system, Property 8: Multiple readings preservation
@given(equipment=equipment_strategy, readings=st.lists(sensor_reading_strategy, min_size=1, max_size=10))
@settings(max_examples=100)
def test_property_8_multiple_readings_preservation(equipment, readings):
    """
    Property 8: Multiple readings preservation
    For any set of sensor readings submitted to the system, 
    all readings should be retrievable from the database
    
    Validates: Requirements 2.4
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    sensor_repo = SensorDataRepository(db)
    
    try:
        # First create equipment
        equipment_repo.create(equipment)
        
        # Store multiple readings
        stored_count = 0
        for reading in readings:
            sensor_reading = {
                'equipment_id': equipment['equipment_id'],
                'sensor_type': reading['sensor_type'],
                'value': reading['value'],
                'unit': reading['unit'],
                'timestamp': datetime.now().isoformat()
            }
            result_id = sensor_repo.create(sensor_reading)
            assert result_id > 0
            stored_count += 1
        
        # Query all readings for this equipment
        retrieved_readings = sensor_repo.get_by_equipment(equipment['equipment_id'], limit=1000)
        
        # Verify all readings are retrievable
        assert len(retrieved_readings) >= stored_count, \
            f"Expected at least {stored_count} readings, but got {len(retrieved_readings)}"
    finally:
        cleanup_test_db(db, db_path)
