"""
Property-Based Tests for Query Operations
Tests equipment query completeness, time range filtering, and multi-criteria filtering
"""

import pytest
import os
import time
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from datetime import datetime, timedelta

from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository


# Test database setup
TEST_DB = "test_queries.db"


@pytest.fixture(scope="function")
def db_manager():
    """Create a fresh database for each test"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    db = DatabaseManager(TEST_DB)
    db.init_schema("schema.sql")
    yield db
    db.close()
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture
def equipment_repo(db_manager):
    """Create equipment repository"""
    return EquipmentRepository(db_manager)


@pytest.fixture
def sensor_repo(db_manager):
    """Create sensor data repository"""
    return SensorDataRepository(db_manager)


# Hypothesis strategies
equipment_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=1,
    max_size=20
)

sensor_type_strategy = st.sampled_from([
    'temperature', 'pressure', 'vibration', 'flow_rate', 
    'rpm', 'voltage', 'current', 'humidity'
])


# Feature: industrial-monitoring-system, Property 10: Equipment query completeness
@given(
    name=st.text(min_size=1, max_size=50),
    equipment_type=st.sampled_from(['pump', 'motor', 'conveyor', 'sensor']),
    location=st.text(min_size=1, max_size=50)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_equipment_query_completeness(name, equipment_type, location, equipment_repo):
    """
    Property 10: Equipment query completeness
    For any equipment that exists in the system, querying by its equipment_id should return the equipment details
    
    Validates: Requirements 3.1
    """
    # Create unique equipment_id using timestamp and counter
    equipment_id = f"EQ-{int(time.time() * 1000000)}"
    
    # Create equipment
    equipment_data = {
        'equipment_id': equipment_id,
        'name': name,
        'type': equipment_type,
        'location': location
    }
    
    equipment_repo.create(equipment_data)
    
    # Query equipment by ID
    retrieved = equipment_repo.get_by_id(equipment_id)
    
    # Property: Equipment should be retrievable
    assert retrieved is not None, f"Equipment {equipment_id} should be retrievable"
    assert retrieved['equipment_id'] == equipment_id
    assert retrieved['name'] == name
    assert retrieved['type'] == equipment_type
    assert retrieved['location'] == location


# Feature: industrial-monitoring-system, Property 11: Time range filtering accuracy
@given(
    sensor_type=sensor_type_strategy,
    num_readings=st.integers(min_value=1, max_value=10),
    query_offset_hours=st.integers(min_value=0, max_value=48)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_time_range_filtering_accuracy(sensor_type, num_readings, query_offset_hours,
                                       db_manager, equipment_repo, sensor_repo):
    """
    Property 11: Time range filtering accuracy
    For any time range query, all returned sensor readings should have timestamps within the specified range,
    and all readings within the range should be returned
    
    Validates: Requirements 3.2
    """
    # Create unique equipment_id using timestamp
    equipment_id = f"EQ-{int(time.time() * 1000000)}"
    
    # Create equipment first
    equipment_data = {
        'equipment_id': equipment_id,
        'name': f'Test Equipment {equipment_id}',
        'type': 'pump',
        'location': 'Test Location'
    }
    
    equipment_repo.create(equipment_data)
    
    # Create sensor readings at different times
    base_time = datetime.now()
    created_readings = []
    
    for i in range(num_readings):
        timestamp = base_time - timedelta(hours=i * 2)
        reading = {
            'equipment_id': equipment_id,
            'sensor_type': sensor_type,
            'value': float(i * 10),
            'timestamp': timestamp.isoformat()
        }
        sensor_repo.create(reading)
        created_readings.append((timestamp, reading))
    
    # Define query time range
    end_time = base_time
    start_time = base_time - timedelta(hours=query_offset_hours)
    
    # Query readings in time range
    results = sensor_repo.get_by_date_range(start_time, end_time, equipment_id=equipment_id)
    
    # Property 1: All returned readings should be within the time range
    for result in results:
        result_time = datetime.fromisoformat(result['timestamp'])
        assert start_time <= result_time <= end_time, \
            f"Reading timestamp {result_time} should be within range [{start_time}, {end_time}]"
    
    # Property 2: All readings within the range should be returned
    expected_in_range = [
        r for t, r in created_readings 
        if start_time <= t <= end_time
    ]
    
    assert len(results) == len(expected_in_range), \
        f"Should return {len(expected_in_range)} readings in range, got {len(results)}"


# Feature: industrial-monitoring-system, Property 12: Multi-criteria filtering correctness
@given(
    sensor_type=sensor_type_strategy,
    other_sensor_type=sensor_type_strategy,
    num_readings=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_multi_criteria_filtering_correctness(sensor_type, other_sensor_type, num_readings,
                                              db_manager, equipment_repo, sensor_repo):
    """
    Property 12: Multi-criteria filtering correctness
    For any sensor data query with filters (equipment_id, sensor_type, date range),
    all returned results should match all specified filter criteria
    
    Validates: Requirements 3.3
    """
    assume(sensor_type != other_sensor_type)  # Ensure we have different sensor types
    
    # Create unique equipment_id using timestamp
    equipment_id = f"EQ-{int(time.time() * 1000000)}"
    
    # Create equipment first
    equipment_data = {
        'equipment_id': equipment_id,
        'name': f'Test Equipment {equipment_id}',
        'type': 'pump',
        'location': 'Test Location'
    }
    
    equipment_repo.create(equipment_data)
    
    # Create readings with target sensor type
    base_time = datetime.now()
    for i in range(num_readings):
        reading = {
            'equipment_id': equipment_id,
            'sensor_type': sensor_type,
            'value': float(i * 10),
            'timestamp': (base_time - timedelta(hours=i)).isoformat()
        }
        sensor_repo.create(reading)
    
    # Create readings with different sensor type (should not be returned)
    for i in range(num_readings):
        reading = {
            'equipment_id': equipment_id,
            'sensor_type': other_sensor_type,
            'value': float(i * 20),
            'timestamp': (base_time - timedelta(hours=i)).isoformat()
        }
        sensor_repo.create(reading)
    
    # Query with multiple filters
    start_time = base_time - timedelta(hours=num_readings * 2)
    end_time = base_time
    
    results = sensor_repo.get_readings_by_filters(
        equipment_id=equipment_id,
        sensor_type=sensor_type,
        start_date=start_time,
        end_date=end_time
    )
    
    # Property: All results should match ALL filter criteria
    assert len(results) > 0, "Should return at least some results"
    
    for result in results:
        # Check equipment_id filter
        assert result['equipment_id'] == equipment_id, \
            f"Result equipment_id {result['equipment_id']} should match filter {equipment_id}"
        
        # Check sensor_type filter
        assert result['sensor_type'] == sensor_type, \
            f"Result sensor_type {result['sensor_type']} should match filter {sensor_type}"
        
        # Check date range filter
        result_time = datetime.fromisoformat(result['timestamp'])
        assert start_time <= result_time <= end_time, \
            f"Result timestamp {result_time} should be within range [{start_time}, {end_time}]"
    
    # Verify we got the expected number of readings (only target sensor type)
    assert len(results) == num_readings, \
        f"Should return {num_readings} readings with sensor_type={sensor_type}, got {len(results)}"
