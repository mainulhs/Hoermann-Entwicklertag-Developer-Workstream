"""
Property-based tests for dashboard display
Tests Properties 22, 23, and 24 from the design document
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import tempfile
import os
from datetime import datetime, timedelta

from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository
from repositories.alerts import AlertRepository
from services.equipment_manager import EquipmentManager
from services.alert_generator import AlertGenerator


# Strategy for generating valid equipment data
equipment_strategy = st.fixed_dictionaries({
    'equipment_id': st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
    )),
    'name': st.text(min_size=1, max_size=100),
    'type': st.sampled_from(['pump', 'motor', 'conveyor', 'sensor', 'compressor', 'valve', 'tank']),
    'location': st.text(min_size=1, max_size=100)
})


# Strategy for generating sensor readings
sensor_reading_strategy = st.fixed_dictionaries({
    'sensor_type': st.sampled_from(['temperature', 'pressure', 'vibration', 'flow_rate', 'humidity']),
    'value': st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    'unit': st.sampled_from(['celsius', 'psi', 'mm/s', 'L/min', '%'])
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


# Feature: industrial-monitoring-system, Property 22: Dashboard equipment completeness
@given(equipment_list=st.lists(equipment_strategy, min_size=1, max_size=10, unique_by=lambda x: x['equipment_id']))
@settings(max_examples=100)
def test_property_22_dashboard_equipment_completeness(equipment_list):
    """
    Property 22: Dashboard equipment completeness
    For any set of registered equipment, the dashboard should display all equipment items
    
    Validates: Requirements 6.1
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    equipment_manager = EquipmentManager(equipment_repo)
    
    try:
        # Register all equipment
        registered_ids = set()
        for equipment in equipment_list:
            result = equipment_manager.register_equipment(equipment)
            if result.success:
                registered_ids.add(equipment['equipment_id'])
        
        # Get all equipment from dashboard (simulating dashboard query)
        dashboard_equipment = equipment_manager.list_all_equipment()
        dashboard_ids = {eq['equipment_id'] for eq in dashboard_equipment}
        
        # Verify all registered equipment appears in dashboard
        assert registered_ids == dashboard_ids, \
            f"Dashboard missing equipment. Expected: {registered_ids}, Got: {dashboard_ids}"
        
        # Verify count matches
        assert len(dashboard_equipment) == len(registered_ids), \
            f"Dashboard equipment count mismatch. Expected: {len(registered_ids)}, Got: {len(dashboard_equipment)}"
        
    finally:
        cleanup_test_db(db, db_path)


# Feature: industrial-monitoring-system, Property 23: Latest sensor reading display
@given(
    equipment=equipment_strategy,
    readings=st.lists(sensor_reading_strategy, min_size=2, max_size=10)
)
@settings(max_examples=100)
def test_property_23_latest_sensor_reading_display(equipment, readings):
    """
    Property 23: Latest sensor reading display
    For any equipment with sensor readings, the dashboard should display 
    the most recent reading based on timestamp
    
    Validates: Requirements 6.2
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    sensor_repo = SensorDataRepository(db)
    equipment_manager = EquipmentManager(equipment_repo)
    
    try:
        # Register equipment
        result = equipment_manager.register_equipment(equipment)
        assume(result.success)
        
        equipment_id = equipment['equipment_id']
        
        # Record sensor readings with different timestamps
        base_time = datetime.now()
        recorded_readings = []
        
        for i, reading in enumerate(readings):
            reading_data = {
                'equipment_id': equipment_id,
                'sensor_type': reading['sensor_type'],
                'value': reading['value'],
                'unit': reading['unit']
            }
            
            # Create reading with specific timestamp (older to newer)
            reading_id = sensor_repo.create(reading_data)
            
            # Get the created reading to see its timestamp
            all_readings = sensor_repo.get_by_equipment(equipment_id, limit=100)
            created_reading = next((r for r in all_readings if r['id'] == reading_id), None)
            if created_reading:
                recorded_readings.append(created_reading)
        
        # Get latest reading (simulating dashboard query)
        latest_readings = sensor_repo.get_by_equipment(equipment_id, limit=1)
        
        if latest_readings:
            latest_reading = latest_readings[0]
            
            # Verify this is indeed the most recent reading
            # All other readings should have timestamps <= latest reading timestamp
            latest_timestamp = datetime.fromisoformat(latest_reading['timestamp'])
            
            for reading in recorded_readings:
                reading_timestamp = datetime.fromisoformat(reading['timestamp'])
                assert reading_timestamp <= latest_timestamp, \
                    f"Found reading with timestamp {reading_timestamp} newer than 'latest' {latest_timestamp}"
            
            # Verify the latest reading is in our recorded readings
            assert latest_reading['id'] in [r['id'] for r in recorded_readings], \
                "Latest reading not found in recorded readings"
        
    finally:
        cleanup_test_db(db, db_path)


# Feature: industrial-monitoring-system, Property 24: Active alert visibility
@given(
    equipment_list=st.lists(equipment_strategy, min_size=1, max_size=5, unique_by=lambda x: x['equipment_id']),
    alert_count=st.integers(min_value=1, max_value=10),
    severities=st.lists(st.sampled_from(['low', 'medium', 'high', 'critical']), min_size=1, max_size=10)
)
@settings(max_examples=100)
def test_property_24_active_alert_visibility(equipment_list, alert_count, severities):
    """
    Property 24: Active alert visibility
    For any active (unacknowledged) alerts in the system, 
    they should be displayed on the dashboard
    
    Validates: Requirements 6.3
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    alert_repo = AlertRepository(db)
    equipment_manager = EquipmentManager(equipment_repo)
    alert_generator = AlertGenerator(alert_repo, equipment_repo)
    
    try:
        # Register equipment
        registered_equipment = []
        for equipment in equipment_list:
            result = equipment_manager.register_equipment(equipment)
            if result.success:
                registered_equipment.append(equipment['equipment_id'])
        
        assume(len(registered_equipment) > 0)
        
        # Generate alerts for random equipment
        generated_alert_ids = set()
        for i in range(min(alert_count, len(registered_equipment) * 3)):
            equipment_id = registered_equipment[i % len(registered_equipment)]
            severity = severities[i % len(severities)]
            
            alert_id = alert_generator.generate_alert(
                equipment_id=equipment_id,
                alert_type='threshold_exceeded',
                severity=severity,
                message=f'Test alert {i}'
            )
            generated_alert_ids.add(alert_id)
        
        # Get active alerts (simulating dashboard query)
        active_alerts = alert_generator.get_active_alerts()
        active_alert_ids = {alert['id'] for alert in active_alerts}
        
        # Verify all generated alerts appear in active alerts
        assert generated_alert_ids.issubset(active_alert_ids), \
            f"Dashboard missing alerts. Expected: {generated_alert_ids}, Got: {active_alert_ids}"
        
        # Verify all displayed alerts are actually active (not acknowledged)
        for alert in active_alerts:
            if alert['id'] in generated_alert_ids:
                assert alert['status'] == 'active', \
                    f"Alert {alert['id']} displayed but status is {alert['status']}, not 'active'"
        
        # Now acknowledge one alert and verify it's no longer in active alerts
        if generated_alert_ids:
            alert_to_ack = list(generated_alert_ids)[0]
            alert_generator.acknowledge_alert(alert_to_ack, 'test_user')
            
            # Get active alerts again
            active_alerts_after = alert_generator.get_active_alerts()
            active_alert_ids_after = {alert['id'] for alert in active_alerts_after}
            
            # Acknowledged alert should not appear in active alerts
            assert alert_to_ack not in active_alert_ids_after, \
                f"Acknowledged alert {alert_to_ack} still appears in active alerts"
        
    finally:
        cleanup_test_db(db, db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
