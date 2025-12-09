"""
Property-based tests for equipment operations
Tests Properties 1, 2, and 3 from the design document
"""

import pytest
from hypothesis import given, strategies as st, settings
import tempfile
import os

from database import DatabaseManager
from repositories.equipment import EquipmentRepository


# Strategy for generating valid equipment data
equipment_strategy = st.fixed_dictionaries({
    'equipment_id': st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
    )),
    'name': st.text(min_size=1, max_size=100),
    'type': st.sampled_from(['pump', 'motor', 'conveyor', 'sensor', 'compressor', 'valve']),
    'location': st.text(min_size=1, max_size=100)
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


# Feature: industrial-monitoring-system, Property 1: Required field validation
@given(equipment=equipment_strategy)
@settings(max_examples=100)
def test_property_1_required_field_validation(equipment):
    """
    Property 1: Required field validation
    For any equipment registration attempt, if any required field 
    (equipment_id, name, type, location) is missing, the validation should reject the registration
    
    Validates: Requirements 1.1
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    
    try:
        # Test with all required fields present - should succeed
        result_id = equipment_repo.create(equipment)
        assert result_id > 0
        
        # Clean up for next test
        equipment_repo.delete(equipment['equipment_id'])
        
        # Test with each required field missing - should fail
        required_fields = ['equipment_id', 'name', 'type', 'location']
        
        for field_to_remove in required_fields:
            incomplete_equipment = equipment.copy()
            del incomplete_equipment[field_to_remove]
            
            with pytest.raises(KeyError):
                equipment_repo.create(incomplete_equipment)
    finally:
        cleanup_test_db(db, db_path)


# Feature: industrial-monitoring-system, Property 2: Equipment registration round-trip
@given(equipment=equipment_strategy)
@settings(max_examples=100)
def test_property_2_equipment_registration_roundtrip(equipment):
    """
    Property 2: Equipment registration round-trip
    For any valid equipment data, after successful registration, 
    querying by equipment_id should return equivalent equipment data
    
    Validates: Requirements 1.2
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    
    try:
        # Register equipment
        result_id = equipment_repo.create(equipment)
        assert result_id > 0
        
        # Query equipment
        retrieved = equipment_repo.get_by_id(equipment['equipment_id'])
        
        # Verify equivalence
        assert retrieved is not None
        assert retrieved['equipment_id'] == equipment['equipment_id']
        assert retrieved['name'] == equipment['name']
        assert retrieved['type'] == equipment['type']
        assert retrieved['location'] == equipment['location']
        
        # Clean up
        equipment_repo.delete(equipment['equipment_id'])
    finally:
        cleanup_test_db(db, db_path)


# Feature: industrial-monitoring-system, Property 3: Duplicate equipment_id rejection
@given(equipment=equipment_strategy)
@settings(max_examples=100)
def test_property_3_duplicate_equipment_id_rejection(equipment):
    """
    Property 3: Duplicate equipment_id rejection
    For any equipment that has been successfully registered, 
    attempting to register another equipment with the same equipment_id should be rejected with an error
    
    Validates: Requirements 1.3
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    
    try:
        # Register equipment first time
        result_id = equipment_repo.create(equipment)
        assert result_id > 0
        
        # Attempt to register with same equipment_id should fail
        duplicate_equipment = equipment.copy()
        duplicate_equipment['name'] = 'Different Name'
        duplicate_equipment['location'] = 'Different Location'
        
        with pytest.raises(Exception):  # SQLite will raise IntegrityError for UNIQUE constraint
            equipment_repo.create(duplicate_equipment)
        
        # Clean up
        equipment_repo.delete(equipment['equipment_id'])
    finally:
        cleanup_test_db(db, db_path)
