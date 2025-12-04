"""
Property-Based Tests for Maintenance Operations
Tests maintenance record round-trip, updates, filtering, overdue detection, and history completeness
"""

import pytest
import os
import time
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, date, timedelta

from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from repositories.maintenance import MaintenanceRepository


# Test database setup
TEST_DB = "test_maintenance.db"


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
def maintenance_repo(db_manager):
    """Create maintenance repository"""
    return MaintenanceRepository(db_manager)


# Hypothesis strategies
maintenance_type_strategy = st.sampled_from([
    'preventive', 'corrective', 'inspection', 'calibration', 'repair'
])


# Feature: industrial-monitoring-system, Property 13: Maintenance record round-trip
@given(
    maintenance_type=maintenance_type_strategy,
    days_ahead=st.integers(min_value=1, max_value=30),
    description=st.text(min_size=1, max_size=100)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_maintenance_record_roundtrip(maintenance_type, days_ahead, description,
                                     equipment_repo, maintenance_repo):
    """
    Property 13: Maintenance record round-trip
    For any maintenance record created, querying maintenance records should return a record
    with equivalent data (equipment_id, maintenance_type, scheduled_date, description)
    
    Validates: Requirements 4.1
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
    
    # Create maintenance record
    scheduled_date = (date.today() + timedelta(days=days_ahead)).isoformat()
    maintenance_data = {
        'equipment_id': equipment_id,
        'maintenance_type': maintenance_type,
        'scheduled_date': scheduled_date,
        'description': description
    }
    
    maintenance_id = maintenance_repo.create(maintenance_data)
    
    # Query maintenance record
    retrieved = maintenance_repo.get_by_id(maintenance_id)
    
    # Property: Maintenance record should be retrievable with equivalent data
    assert retrieved is not None, f"Maintenance record {maintenance_id} should be retrievable"
    assert retrieved['equipment_id'] == equipment_id
    assert retrieved['maintenance_type'] == maintenance_type
    assert retrieved['scheduled_date'] == scheduled_date
    assert retrieved['description'] == description


# Feature: industrial-monitoring-system, Property 14: Maintenance update persistence
@given(
    maintenance_type=maintenance_type_strategy,
    days_ahead=st.integers(min_value=1, max_value=30),
    technician_notes=st.text(min_size=1, max_size=100)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_maintenance_update_persistence(maintenance_type, days_ahead, technician_notes,
                                       equipment_repo, maintenance_repo):
    """
    Property 14: Maintenance update persistence
    For any maintenance record, after updating with completion_date and technician_notes,
    querying the record should return the updated values
    
    Validates: Requirements 4.2
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
    
    # Create maintenance record
    scheduled_date = (date.today() + timedelta(days=days_ahead)).isoformat()
    maintenance_data = {
        'equipment_id': equipment_id,
        'maintenance_type': maintenance_type,
        'scheduled_date': scheduled_date,
        'description': 'Initial description'
    }
    
    maintenance_id = maintenance_repo.create(maintenance_data)
    
    # Update maintenance record
    completion_date = date.today().isoformat()
    update_data = {
        'completion_date': completion_date,
        'technician_notes': technician_notes,
        'status': 'completed'
    }
    
    success = maintenance_repo.update(maintenance_id, update_data)
    assert success, "Update should succeed"
    
    # Query updated maintenance record
    retrieved = maintenance_repo.get_by_id(maintenance_id)
    
    # Property: Updated values should be persisted
    assert retrieved is not None
    assert retrieved['completion_date'] == completion_date
    assert retrieved['technician_notes'] == technician_notes
    assert retrieved['status'] == 'completed'


# Feature: industrial-monitoring-system, Property 15: Maintenance filtering correctness
@given(
    maintenance_type=maintenance_type_strategy,
    num_records=st.integers(min_value=2, max_value=5),
    days_range=st.integers(min_value=10, max_value=30)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_maintenance_filtering_correctness(maintenance_type, num_records, days_range,
                                          equipment_repo, maintenance_repo):
    """
    Property 15: Maintenance filtering correctness
    For any maintenance query with filters (equipment_id, date range),
    all returned results should match the specified criteria
    
    Validates: Requirements 4.3
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
    
    # Create maintenance records within date range
    start_date = date.today()
    end_date = start_date + timedelta(days=days_range)
    
    for i in range(num_records):
        scheduled_date = (start_date + timedelta(days=i * (days_range // num_records))).isoformat()
        maintenance_data = {
            'equipment_id': equipment_id,
            'maintenance_type': maintenance_type,
            'scheduled_date': scheduled_date,
            'description': f'Maintenance {i}'
        }
        maintenance_repo.create(maintenance_data)
    
    # Query with filters
    results = maintenance_repo.get_by_equipment(
        equipment_id=equipment_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Property: All results should match filter criteria
    assert len(results) == num_records, f"Should return {num_records} records"
    
    for result in results:
        # Check equipment_id filter
        assert result['equipment_id'] == equipment_id
        
        # Check date range filter
        result_date = date.fromisoformat(result['scheduled_date'])
        assert start_date <= result_date <= end_date


# Feature: industrial-monitoring-system, Property 16: Overdue maintenance detection
@given(
    maintenance_type=maintenance_type_strategy,
    days_past=st.integers(min_value=1, max_value=30)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_overdue_maintenance_detection(maintenance_type, days_past,
                                       equipment_repo, maintenance_repo):
    """
    Property 16: Overdue maintenance detection
    For any maintenance record where scheduled_date is in the past and status is not 'completed',
    the record should be flagged as overdue
    
    Validates: Requirements 4.4
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
    
    # Create overdue maintenance record (scheduled in the past)
    scheduled_date = (date.today() - timedelta(days=days_past)).isoformat()
    maintenance_data = {
        'equipment_id': equipment_id,
        'maintenance_type': maintenance_type,
        'scheduled_date': scheduled_date,
        'description': 'Overdue maintenance',
        'status': 'scheduled'  # Not completed
    }
    
    maintenance_id = maintenance_repo.create(maintenance_data)
    
    # Query overdue maintenance
    overdue_records = maintenance_repo.get_overdue()
    
    # Property: Overdue record should be in the overdue list
    overdue_ids = [record['id'] for record in overdue_records]
    assert maintenance_id in overdue_ids, "Overdue maintenance should be detected"
    
    # Verify the overdue record details
    overdue_record = next(r for r in overdue_records if r['id'] == maintenance_id)
    assert overdue_record['equipment_id'] == equipment_id
    assert overdue_record['status'] != 'completed'
    assert date.fromisoformat(overdue_record['scheduled_date']) < date.today()


# Feature: industrial-monitoring-system, Property 17: Equipment maintenance history completeness
@given(
    num_records=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_equipment_maintenance_history_completeness(num_records, equipment_repo, maintenance_repo):
    """
    Property 17: Equipment maintenance history completeness
    For any equipment, querying its maintenance history should return all maintenance records
    associated with that equipment_id
    
    Validates: Requirements 4.5
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
    
    # Create multiple maintenance records for this equipment
    created_ids = []
    for i in range(num_records):
        scheduled_date = (date.today() + timedelta(days=i * 7)).isoformat()
        maintenance_data = {
            'equipment_id': equipment_id,
            'maintenance_type': 'preventive',
            'scheduled_date': scheduled_date,
            'description': f'Maintenance {i}'
        }
        maintenance_id = maintenance_repo.create(maintenance_data)
        created_ids.append(maintenance_id)
    
    # Query equipment maintenance history
    history = maintenance_repo.get_by_equipment(equipment_id)
    
    # Property: All maintenance records for equipment should be returned
    assert len(history) == num_records, f"Should return all {num_records} maintenance records"
    
    history_ids = [record['id'] for record in history]
    for created_id in created_ids:
        assert created_id in history_ids, f"Maintenance record {created_id} should be in history"
    
    # Verify all records belong to the correct equipment
    for record in history:
        assert record['equipment_id'] == equipment_id
