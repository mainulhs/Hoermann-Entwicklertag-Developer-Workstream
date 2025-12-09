"""
New Property-Based Tests for Alert Generation
Tests alert threshold logic and severity calculation
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
import tempfile
import os

from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository
from repositories.alerts import AlertRepository
from services.sensor_processor import SensorProcessor
from services.alert_generator import AlertGenerator


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


# Property: Alert severity increases with threshold violation percentage
@given(
    sensor_type=st.sampled_from(['temperature', 'pressure', 'vibration']),
    base_value=st.floats(min_value=50.0, max_value=100.0, allow_nan=False),
    violation_percent=st.floats(min_value=5.0, max_value=100.0, allow_nan=False)
)
@settings(max_examples=50)
def test_alert_severity_increases_with_violation(sensor_type, base_value, violation_percent):
    """
    Property: Alert severity should increase with threshold violation percentage
    
    For any sensor reading that exceeds threshold by X%, 
    the severity should be higher than a reading that exceeds by X/2%
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    sensor_repo = SensorDataRepository(db)
    
    try:
        # Create equipment
        equipment_data = {
            'equipment_id': 'TEST-001',
            'name': 'Test Equipment',
            'type': 'pump',
            'location': 'Test Location'
        }
        equipment_repo.create(equipment_data)
        
        # Set thresholds
        thresholds = {
            'temperature': {'max': base_value},
            'pressure': {'max': base_value},
            'vibration': {'max': base_value}
        }
        
        processor = SensorProcessor(sensor_repo, equipment_repo, thresholds)
        
        # Test small violation
        small_violation = base_value * (1 + violation_percent / 200)  # Half the violation
        reading1 = {
            'equipment_id': 'TEST-001',
            'sensor_type': sensor_type,
            'value': small_violation,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test large violation
        large_violation = base_value * (1 + violation_percent / 100)  # Full violation
        reading2 = {
            'equipment_id': 'TEST-001',
            'sensor_type': sensor_type,
            'value': large_violation,
            'timestamp': datetime.now().isoformat()
        }
        
        # Process readings
        result1 = processor.record_reading(reading1)
        result2 = processor.record_reading(reading2)
        
        # Both should generate alerts if they exceed threshold
        if result1.success and result1.data['alert'] and result2.success and result2.data['alert']:
            severity1 = result1.data['alert']['severity']
            severity2 = result2.data['alert']['severity']
            
            # Map severity to numeric values
            severity_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            
            # Property: Larger violation should have equal or higher severity
            assert severity_order[severity2] >= severity_order[severity1], \
                f"Larger violation ({large_violation}) should have higher severity than smaller ({small_violation})"
    
    finally:
        cleanup_test_db(db, db_path)


# Property: Round-trip property for equipment updates
@given(
    equipment_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
    )),
    name=st.text(min_size=1, max_size=50),
    location=st.text(min_size=1, max_size=50),
    equipment_type=st.sampled_from(['pump', 'motor', 'conveyor', 'compressor'])
)
@settings(max_examples=50)
def test_equipment_update_roundtrip(equipment_id, name, location, equipment_type):
    """
    Property: Equipment update round-trip
    
    For any equipment update, the updated values should be retrievable
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    
    try:
        # Create initial equipment
        original_data = {
            'equipment_id': equipment_id,
            'name': 'Original Name',
            'type': equipment_type,
            'location': 'Original Location'
        }
        equipment_repo.create(original_data)
        
        # Update equipment
        update_data = {
            'name': name,
            'location': location,
            'type': equipment_type
        }
        success = equipment_repo.update(equipment_id, update_data)
        assert success, "Equipment update should succeed"
        
        # Retrieve updated equipment
        retrieved = equipment_repo.get_by_id(equipment_id)
        
        # Property: Updated values should match
        assert retrieved is not None
        assert retrieved['name'] == name
        assert retrieved['location'] == location
        assert retrieved['type'] == equipment_type
        assert retrieved['equipment_id'] == equipment_id  # ID should not change
    
    finally:
        cleanup_test_db(db, db_path)


# Property: Threshold boundaries are correctly handled
@given(
    threshold_value=st.floats(min_value=10.0, max_value=100.0, allow_nan=False),
    offset=st.floats(min_value=-0.1, max_value=0.1, allow_nan=False)
)
@settings(max_examples=50)
def test_threshold_boundary_handling(threshold_value, offset):
    """
    Property: Threshold boundary handling
    
    Values exactly at threshold should not generate alerts,
    values above threshold should generate alerts
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    sensor_repo = SensorDataRepository(db)
    
    try:
        # Create equipment
        equipment_data = {
            'equipment_id': 'BOUNDARY-TEST',
            'name': 'Boundary Test Equipment',
            'type': 'pump',
            'location': 'Test Location'
        }
        equipment_repo.create(equipment_data)
        
        # Set threshold
        thresholds = {
            'temperature': {'max': threshold_value, 'min': 0.0}
        }
        
        processor = SensorProcessor(sensor_repo, equipment_repo, thresholds)
        
        # Test value near threshold
        test_value = threshold_value + offset
        reading = {
            'equipment_id': 'BOUNDARY-TEST',
            'sensor_type': 'temperature',
            'value': test_value,
            'timestamp': datetime.now().isoformat()
        }
        
        result = processor.record_reading(reading)
        assert result.success
        
        # Property: Alert generation should match threshold logic
        should_alert = test_value > threshold_value
        alert_generated = result.data['alert'] is not None
        
        assert alert_generated == should_alert, \
            f"Value {test_value} vs threshold {threshold_value}: expected alert={should_alert}, got={alert_generated}"
    
    finally:
        cleanup_test_db(db, db_path)