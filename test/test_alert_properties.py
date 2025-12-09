"""
Property-Based Tests for Alert Operations
Tests threshold alert generation and alert management
"""

import pytest
import os
import time
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime

from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository
from repositories.alerts import AlertRepository
from services.sensor_processor import SensorProcessor
from services.alert_generator import AlertGenerator


# Test database setup
TEST_DB = "test_alerts.db"


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


@pytest.fixture
def alert_repo(db_manager):
    """Create alert repository"""
    return AlertRepository(db_manager)


@pytest.fixture
def sensor_processor(sensor_repo, equipment_repo):
    """Create sensor processor with default thresholds"""
    return SensorProcessor(sensor_repo, equipment_repo)


@pytest.fixture
def alert_generator(alert_repo, equipment_repo):
    """Create alert generator"""
    return AlertGenerator(alert_repo, equipment_repo)


# Hypothesis strategies for generating test data
equipment_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=1,
    max_size=20
)

sensor_type_strategy = st.sampled_from([
    'temperature', 'pressure', 'vibration', 'flow_rate', 
    'rpm', 'voltage', 'current', 'humidity'
])


# Feature: industrial-monitoring-system, Property 9: Threshold alert generation
@given(
    equipment_id=equipment_id_strategy,
    sensor_type=sensor_type_strategy,
    value=st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_threshold_alert_generation(equipment_id, sensor_type, value, 
                                   db_manager, equipment_repo, sensor_repo, alert_repo):
    """
    Property 9: Threshold alert generation
    For any sensor reading where the value exceeds the configured threshold for that sensor type,
    an alert should be generated
    
    Validates: Requirements 2.5, 5.1
    """
    # Create equipment first
    equipment_data = {
        'equipment_id': equipment_id,
        'name': f'Test Equipment {equipment_id}',
        'type': 'pump',
        'location': 'Test Location'
    }
    
    try:
        equipment_repo.create(equipment_data)
    except:
        # Equipment might already exist from previous example
        pass
    
    # Create sensor processor with known thresholds
    thresholds = {
        'temperature': {'max': 80.0, 'min': -10.0},
        'pressure': {'max': 150.0, 'min': 0.0},
        'vibration': {'max': 10.0, 'min': 0.0},
        'flow_rate': {'max': 1000.0, 'min': 0.0},
        'rpm': {'max': 5000.0, 'min': 0.0},
        'voltage': {'max': 250.0, 'min': 0.0},
        'current': {'max': 100.0, 'min': 0.0},
        'humidity': {'max': 100.0, 'min': 0.0}
    }
    
    processor = SensorProcessor(sensor_repo, equipment_repo, thresholds)
    alert_gen = AlertGenerator(alert_repo, equipment_repo)
    
    # Create sensor reading
    reading = {
        'equipment_id': equipment_id,
        'sensor_type': sensor_type,
        'value': value,
        'timestamp': datetime.now().isoformat()
    }
    
    # Record reading and check for alert
    result = processor.record_reading(reading)
    assert result.success
    
    # Determine if alert should be generated
    threshold_config = thresholds[sensor_type]
    should_alert = (value > threshold_config['max']) or (value < threshold_config['min'])
    
    # Check if alert was generated
    alert_generated = result.data['alert'] is not None
    
    # Property: If threshold exceeded, alert should be generated
    if should_alert:
        assert alert_generated, f"Alert should be generated for {sensor_type}={value} (thresholds: {threshold_config})"
        
        # If alert was generated, store it in the database
        alert_data = result.data['alert']
        alert_id = alert_gen.generate_alert(
            equipment_id=alert_data['equipment_id'],
            alert_type=alert_data['alert_type'],
            severity=alert_data['severity'],
            message=alert_data['message']
        )
        
        # Verify alert was stored in database
        equipment_alerts = alert_repo.get_by_equipment(equipment_id)
        assert len(equipment_alerts) > 0, "Alert should be stored in database"
        
        # Verify alert details
        stored_alert = equipment_alerts[-1]  # Get the most recent alert
        assert stored_alert['equipment_id'] == equipment_id
        assert stored_alert['alert_type'] == 'threshold_exceeded'
        assert stored_alert['severity'] in ['low', 'medium', 'high', 'critical']
    else:
        # If threshold not exceeded, no alert should be generated
        assert not alert_generated, f"No alert should be generated for {sensor_type}={value} (thresholds: {threshold_config})"



# Feature: industrial-monitoring-system, Property 18: Alert record round-trip
@given(
    alert_type=st.sampled_from(['threshold_exceeded', 'equipment_failure', 'maintenance_due']),
    severity=st.sampled_from(['low', 'medium', 'high', 'critical']),
    message=st.text(min_size=1, max_size=100)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_alert_record_roundtrip(alert_type, severity, message, equipment_repo, alert_repo, alert_generator):
    """
    Property 18: Alert record round-trip
    For any alert generated, querying alerts should return an alert with equivalent data
    (equipment_id, alert_type, severity, timestamp)
    
    Validates: Requirements 5.2
    """
    # Create unique equipment
    equipment_id = f"EQ-{int(time.time() * 1000000)}"
    equipment_data = {
        'equipment_id': equipment_id,
        'name': f'Test Equipment {equipment_id}',
        'type': 'pump',
        'location': 'Test Location'
    }
    equipment_repo.create(equipment_data)
    
    # Generate alert
    alert_id = alert_generator.generate_alert(
        equipment_id=equipment_id,
        alert_type=alert_type,
        severity=severity,
        message=message
    )
    
    # Query alert
    retrieved = alert_repo.get_by_id(alert_id)
    
    # Property: Alert should be retrievable with equivalent data
    assert retrieved is not None, f"Alert {alert_id} should be retrievable"
    assert retrieved['equipment_id'] == equipment_id
    assert retrieved['alert_type'] == alert_type
    assert retrieved['severity'] == severity
    assert retrieved['message'] == message


# Feature: industrial-monitoring-system, Property 19: Active alerts filtering and sorting
@given(
    num_alerts=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_active_alerts_filtering_and_sorting(num_alerts, equipment_repo, alert_repo, alert_generator):
    """
    Property 19: Active alerts filtering and sorting
    For any set of alerts in the system, querying active alerts should return only unacknowledged alerts,
    sorted by severity (highest first)
    
    Validates: Requirements 5.3
    """
    # Create unique equipment
    equipment_id = f"EQ-{int(time.time() * 1000000)}"
    equipment_data = {
        'equipment_id': equipment_id,
        'name': f'Test Equipment {equipment_id}',
        'type': 'pump',
        'location': 'Test Location'
    }
    equipment_repo.create(equipment_data)
    
    # Create alerts with different severities
    severities = ['low', 'medium', 'high', 'critical']
    created_alert_ids = []
    
    for i in range(num_alerts):
        severity = severities[i % len(severities)]
        alert_id = alert_generator.generate_alert(
            equipment_id=equipment_id,
            alert_type='threshold_exceeded',
            severity=severity,
            message=f'Alert {i}'
        )
        created_alert_ids.append((alert_id, severity))
    
    # Acknowledge some alerts (make them inactive)
    if num_alerts > 1:
        alert_repo.acknowledge(created_alert_ids[0][0], 'test_user')
    
    # Query active alerts
    active_alerts = alert_generator.get_active_alerts()
    
    # Property 1: Only unacknowledged alerts should be returned
    for alert in active_alerts:
        if alert['equipment_id'] == equipment_id:
            assert alert['status'] == 'active', "Only active alerts should be returned"
    
    # Property 2: Alerts should be sorted by severity (critical > high > medium > low)
    severity_order = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
    equipment_active_alerts = [a for a in active_alerts if a['equipment_id'] == equipment_id]
    
    for i in range(len(equipment_active_alerts) - 1):
        current_severity = equipment_active_alerts[i]['severity']
        next_severity = equipment_active_alerts[i + 1]['severity']
        assert severity_order[current_severity] <= severity_order[next_severity], \
            f"Alerts should be sorted by severity: {current_severity} should come before or equal to {next_severity}"


# Feature: industrial-monitoring-system, Property 20: Alert acknowledgment persistence
@given(
    alert_type=st.sampled_from(['threshold_exceeded', 'equipment_failure']),
    severity=st.sampled_from(['low', 'medium', 'high', 'critical']),
    username=st.text(min_size=1, max_size=20)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_alert_acknowledgment_persistence(alert_type, severity, username,
                                         equipment_repo, alert_repo, alert_generator):
    """
    Property 20: Alert acknowledgment persistence
    For any alert, after acknowledgment, querying the alert should show status as 'acknowledged'
    and include an acknowledgment timestamp
    
    Validates: Requirements 5.4
    """
    # Create unique equipment
    equipment_id = f"EQ-{int(time.time() * 1000000)}"
    equipment_data = {
        'equipment_id': equipment_id,
        'name': f'Test Equipment {equipment_id}',
        'type': 'pump',
        'location': 'Test Location'
    }
    equipment_repo.create(equipment_data)
    
    # Generate alert
    alert_id = alert_generator.generate_alert(
        equipment_id=equipment_id,
        alert_type=alert_type,
        severity=severity,
        message='Test alert'
    )
    
    # Acknowledge alert
    result = alert_generator.acknowledge_alert(alert_id, username)
    assert result.success, "Acknowledgment should succeed"
    
    # Query alert
    retrieved = alert_repo.get_by_id(alert_id)
    
    # Property: Alert should show acknowledged status and timestamp
    assert retrieved is not None
    assert retrieved['status'] == 'acknowledged', "Alert status should be 'acknowledged'"
    assert retrieved['acknowledged_by'] == username, "Alert should record who acknowledged it"
    assert retrieved['acknowledged_at'] is not None, "Alert should have acknowledgment timestamp"


# Feature: industrial-monitoring-system, Property 21: Multiple alert generation
@given(
    num_readings=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_multiple_alert_generation(num_readings, equipment_repo, sensor_repo, alert_repo):
    """
    Property 21: Multiple alert generation
    For any set of sensor readings that exceed thresholds, each reading should generate a separate alert
    (no merging or deduplication)
    
    Validates: Requirements 5.5
    """
    # Create unique equipment
    equipment_id = f"EQ-{int(time.time() * 1000000)}"
    equipment_data = {
        'equipment_id': equipment_id,
        'name': f'Test Equipment {equipment_id}',
        'type': 'pump',
        'location': 'Test Location'
    }
    equipment_repo.create(equipment_data)
    
    # Create sensor processor with known thresholds
    from services.sensor_processor import SensorProcessor
    from services.alert_generator import AlertGenerator
    
    thresholds = {
        'temperature': {'max': 80.0, 'min': -10.0}
    }
    
    processor = SensorProcessor(sensor_repo, equipment_repo, thresholds)
    alert_gen = AlertGenerator(alert_repo, equipment_repo)
    
    # Record multiple readings that exceed threshold
    initial_alert_count = len(alert_repo.get_by_equipment(equipment_id))
    
    for i in range(num_readings):
        reading = {
            'equipment_id': equipment_id,
            'sensor_type': 'temperature',
            'value': 100.0 + i,  # All exceed max threshold of 80.0
            'timestamp': datetime.now().isoformat()
        }
        
        result = processor.record_reading(reading)
        assert result.success
        
        # If alert was generated, store it
        if result.data['alert']:
            alert_data = result.data['alert']
            alert_gen.generate_alert(
                equipment_id=alert_data['equipment_id'],
                alert_type=alert_data['alert_type'],
                severity=alert_data['severity'],
                message=alert_data['message']
            )
    
    # Query alerts for equipment
    alerts = alert_repo.get_by_equipment(equipment_id)
    
    # Property: Each threshold violation should generate a separate alert
    new_alerts = len(alerts) - initial_alert_count
    assert new_alerts == num_readings, \
        f"Should generate {num_readings} separate alerts, got {new_alerts}"
