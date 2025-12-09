"""
Unit tests for Sample Data Generator
Tests that generated data has valid structure and populate_database() works correctly
"""

import pytest
import os
from datetime import datetime, date
from database import DatabaseManager
from utils.sample_data import SampleDataGenerator
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository
from repositories.alerts import AlertRepository
from repositories.maintenance import MaintenanceRepository


@pytest.fixture
def test_db():
    """Create a test database"""
    db_path = "test_sample_data.db"
    
    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    db.init_schema("schema.sql")
    
    yield db
    
    # Cleanup
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def generator(test_db):
    """Create a SampleDataGenerator instance"""
    return SampleDataGenerator(test_db)


def test_generate_equipment_returns_correct_count(generator):
    """Test that generate_equipment returns the requested number of equipment"""
    count = 5
    equipment_list = generator.generate_equipment(count)
    
    assert len(equipment_list) == count


def test_generate_equipment_has_valid_structure(generator):
    """Test that generated equipment has all required fields"""
    equipment_list = generator.generate_equipment(3)
    
    for equipment in equipment_list:
        assert 'equipment_id' in equipment
        assert 'name' in equipment
        assert 'type' in equipment
        assert 'location' in equipment
        assert 'status' in equipment
        
        # Verify field types
        assert isinstance(equipment['equipment_id'], str)
        assert isinstance(equipment['name'], str)
        assert isinstance(equipment['type'], str)
        assert isinstance(equipment['location'], str)
        assert isinstance(equipment['status'], str)
        
        # Verify equipment_id format
        assert '-' in equipment['equipment_id']
        
        # Verify type is valid
        assert equipment['type'] in generator.EQUIPMENT_TYPES
        
        # Verify location is valid
        assert equipment['location'] in generator.LOCATIONS
        
        # Verify status is valid
        assert equipment['status'] in ['active', 'maintenance', 'inactive']


def test_generate_equipment_unique_ids(generator):
    """Test that generated equipment have unique IDs"""
    equipment_list = generator.generate_equipment(10)
    equipment_ids = [eq['equipment_id'] for eq in equipment_list]
    
    assert len(equipment_ids) == len(set(equipment_ids))


def test_generate_sensor_readings_returns_correct_count(generator):
    """Test that generate_sensor_readings returns the requested number of readings"""
    count = 20
    readings = generator.generate_sensor_readings('PUMP-001', 'pump', count)
    
    assert len(readings) == count


def test_generate_sensor_readings_has_valid_structure(generator):
    """Test that generated sensor readings have all required fields"""
    readings = generator.generate_sensor_readings('MOTOR-001', 'motor', 10)
    
    for reading in readings:
        assert 'equipment_id' in reading
        assert 'sensor_type' in reading
        assert 'value' in reading
        assert 'unit' in reading
        assert 'timestamp' in reading
        
        # Verify field types
        assert isinstance(reading['equipment_id'], str)
        assert isinstance(reading['sensor_type'], str)
        assert isinstance(reading['value'], (int, float))
        assert isinstance(reading['unit'], str)
        assert isinstance(reading['timestamp'], str)
        
        # Verify equipment_id matches
        assert reading['equipment_id'] == 'MOTOR-001'
        
        # Verify sensor_type is valid for motor
        assert reading['sensor_type'] in generator.EQUIPMENT_TYPES['motor']
        
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(reading['timestamp'])


def test_generate_alerts_returns_correct_count(generator):
    """Test that generate_alerts returns the requested number of alerts"""
    equipment_ids = ['PUMP-001', 'MOTOR-001', 'CONVEYOR-001']
    count = 15
    alerts = generator.generate_alerts(equipment_ids, count)
    
    assert len(alerts) == count


def test_generate_alerts_has_valid_structure(generator):
    """Test that generated alerts have all required fields"""
    equipment_ids = ['PUMP-001', 'MOTOR-001']
    alerts = generator.generate_alerts(equipment_ids, 10)
    
    for alert in alerts:
        assert 'equipment_id' in alert
        assert 'alert_type' in alert
        assert 'severity' in alert
        assert 'message' in alert
        assert 'status' in alert
        
        # Verify field types
        assert isinstance(alert['equipment_id'], str)
        assert isinstance(alert['alert_type'], str)
        assert isinstance(alert['severity'], str)
        assert isinstance(alert['message'], str)
        assert isinstance(alert['status'], str)
        
        # Verify equipment_id is from provided list
        assert alert['equipment_id'] in equipment_ids
        
        # Verify alert_type is valid
        assert alert['alert_type'] in generator.ALERT_TYPES
        
        # Verify severity is valid
        assert alert['severity'] in generator.SEVERITIES
        
        # Verify status is valid
        assert alert['status'] in ['active', 'acknowledged']


def test_generate_alerts_with_empty_equipment_list(generator):
    """Test that generate_alerts handles empty equipment list"""
    alerts = generator.generate_alerts([], 10)
    
    assert alerts == []


def test_generate_maintenance_records_returns_correct_count(generator):
    """Test that generate_maintenance_records returns the requested number of records"""
    equipment_ids = ['PUMP-001', 'MOTOR-001', 'CONVEYOR-001']
    count = 25
    records = generator.generate_maintenance_records(equipment_ids, count)
    
    assert len(records) == count


def test_generate_maintenance_records_has_valid_structure(generator):
    """Test that generated maintenance records have all required fields"""
    equipment_ids = ['PUMP-001', 'MOTOR-001']
    records = generator.generate_maintenance_records(equipment_ids, 10)
    
    for record in records:
        assert 'equipment_id' in record
        assert 'maintenance_type' in record
        assert 'scheduled_date' in record
        assert 'description' in record
        assert 'status' in record
        
        # Verify field types
        assert isinstance(record['equipment_id'], str)
        assert isinstance(record['maintenance_type'], str)
        assert isinstance(record['scheduled_date'], str)
        assert isinstance(record['description'], str)
        assert isinstance(record['status'], str)
        
        # Verify equipment_id is from provided list
        assert record['equipment_id'] in equipment_ids
        
        # Verify maintenance_type is valid
        assert record['maintenance_type'] in generator.MAINTENANCE_TYPES
        
        # Verify scheduled_date is valid ISO format
        date.fromisoformat(record['scheduled_date'])
        
        # Verify status is valid
        assert record['status'] in ['scheduled', 'in_progress', 'completed']
        
        # If completed, should have completion details
        if record['status'] == 'completed':
            assert 'completion_date' in record or 'technician_notes' in record


def test_generate_maintenance_records_with_empty_equipment_list(generator):
    """Test that generate_maintenance_records handles empty equipment list"""
    records = generator.generate_maintenance_records([], 10)
    
    assert records == []


def test_populate_database_creates_equipment(test_db, generator):
    """Test that populate_database creates equipment records"""
    equipment_repo = EquipmentRepository(test_db)
    
    # Populate with small dataset
    generator.populate_database(
        equipment_count=3,
        readings_per_equipment=5,
        alert_count=2,
        maintenance_count=2
    )
    
    # Verify equipment was created
    all_equipment = equipment_repo.get_all()
    assert len(all_equipment) == 3


def test_populate_database_creates_sensor_readings(test_db, generator):
    """Test that populate_database creates sensor readings"""
    sensor_repo = SensorDataRepository(test_db)
    
    # Populate with small dataset
    generator.populate_database(
        equipment_count=2,
        readings_per_equipment=10,
        alert_count=0,
        maintenance_count=0
    )
    
    # Verify sensor readings were created
    all_readings = sensor_repo.get_all_readings()
    assert len(all_readings) == 20  # 2 equipment * 10 readings each


def test_populate_database_creates_alerts(test_db, generator):
    """Test that populate_database creates alerts"""
    alert_repo = AlertRepository(test_db)
    
    # Populate with small dataset
    generator.populate_database(
        equipment_count=2,
        readings_per_equipment=5,
        alert_count=8,
        maintenance_count=0
    )
    
    # Verify alerts were created
    all_alerts = alert_repo.get_all()
    assert len(all_alerts) == 8


def test_populate_database_creates_maintenance_records(test_db, generator):
    """Test that populate_database creates maintenance records"""
    maintenance_repo = MaintenanceRepository(test_db)
    
    # Populate with small dataset
    generator.populate_database(
        equipment_count=2,
        readings_per_equipment=5,
        alert_count=0,
        maintenance_count=12
    )
    
    # Verify maintenance records were created
    all_maintenance = maintenance_repo.get_all()
    assert len(all_maintenance) == 12


def test_populate_database_with_default_parameters(test_db, generator):
    """Test that populate_database works with default parameters"""
    equipment_repo = EquipmentRepository(test_db)
    sensor_repo = SensorDataRepository(test_db)
    alert_repo = AlertRepository(test_db)
    maintenance_repo = MaintenanceRepository(test_db)
    
    # Populate with default parameters
    generator.populate_database()
    
    # Verify data was created
    assert len(equipment_repo.get_all()) == 10
    assert len(sensor_repo.get_all_readings()) == 500  # 10 equipment * 50 readings
    assert len(alert_repo.get_all()) == 20
    assert len(maintenance_repo.get_all()) == 30


def test_sensor_value_generation_returns_valid_ranges(generator):
    """Test that _generate_sensor_value returns values in expected ranges"""
    # Test known sensor types
    sensor_types = ['temperature', 'pressure', 'vibration', 'flow_rate']
    
    for sensor_type in sensor_types:
        value, unit = generator._generate_sensor_value(sensor_type)
        
        # Verify value is numeric
        assert isinstance(value, (int, float))
        
        # Verify unit is string
        assert isinstance(unit, str)
        assert len(unit) > 0
        
        # Verify value is positive
        assert value >= 0


def test_sensor_value_generation_handles_unknown_sensor_type(generator):
    """Test that _generate_sensor_value handles unknown sensor types"""
    value, unit = generator._generate_sensor_value('unknown_sensor_type')
    
    # Should return default values
    assert isinstance(value, (int, float))
    assert unit == 'units'
    assert 0 <= value <= 100
