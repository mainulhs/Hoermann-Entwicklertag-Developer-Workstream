"""
Round-Trip Property Tests for Equipment Management
Tests the new edit/delete functionality
"""

import pytest
from hypothesis import given, strategies as st, settings
import tempfile
import os

from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from services.equipment_manager import EquipmentManager


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


# Property: Equipment CRUD operations maintain data integrity
@given(
    equipment_id=st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
    )),
    original_name=st.text(min_size=1, max_size=50),
    updated_name=st.text(min_size=1, max_size=50),
    location=st.text(min_size=1, max_size=50),
    equipment_type=st.sampled_from(['pump', 'motor', 'conveyor', 'compressor', 'valve', 'tank'])
)
@settings(max_examples=30)
def test_equipment_crud_roundtrip(equipment_id, original_name, updated_name, location, equipment_type):
    """
    Property: Equipment CRUD round-trip
    
    For any equipment: Create → Read → Update → Read → Delete → Read
    should maintain data integrity at each step
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    equipment_manager = EquipmentManager(equipment_repo)
    
    try:
        # CREATE: Register equipment
        create_data = {
            'equipment_id': equipment_id,
            'name': original_name,
            'type': equipment_type,
            'location': location,
            'status': 'active'
        }
        
        create_result = equipment_manager.register_equipment(create_data)
        assert create_result.success, f"Equipment creation failed: {create_result.error_message}"
        
        # READ: Verify creation
        retrieved = equipment_manager.get_equipment_status(equipment_id)
        assert retrieved['equipment_id'] == equipment_id
        assert retrieved['name'] == original_name
        assert retrieved['type'] == equipment_type
        assert retrieved['location'] == location
        
        # UPDATE: Modify equipment
        update_data = {
            'name': updated_name,
            'location': location,
            'type': equipment_type,
            'status': 'maintenance'
        }
        
        update_result = equipment_manager.update_equipment(equipment_id, update_data)
        assert update_result.success, f"Equipment update failed: {update_result.error_message}"
        
        # READ: Verify update
        updated_retrieved = equipment_manager.get_equipment_status(equipment_id)
        assert updated_retrieved['equipment_id'] == equipment_id  # ID unchanged
        assert updated_retrieved['name'] == updated_name  # Name updated
        assert updated_retrieved['status'] == 'maintenance'  # Status updated
        
        # DELETE: Remove equipment
        delete_result = equipment_manager.delete_equipment(equipment_id)
        assert delete_result.success, f"Equipment deletion failed: {delete_result.error_message}"
        
        # READ: Verify deletion
        with pytest.raises(ValueError):
            equipment_manager.get_equipment_status(equipment_id)
    
    finally:
        cleanup_test_db(db, db_path)


# Property: Equipment list consistency
@given(
    equipment_count=st.integers(min_value=1, max_value=5),
    equipment_type=st.sampled_from(['pump', 'motor', 'conveyor'])
)
@settings(max_examples=20)
def test_equipment_list_consistency(equipment_count, equipment_type):
    """
    Property: Equipment list consistency
    
    For any number of equipment created, list_all_equipment should return
    exactly that many equipment items
    """
    db, db_path = create_test_db()
    equipment_repo = EquipmentRepository(db)
    equipment_manager = EquipmentManager(equipment_repo)
    
    try:
        created_ids = []
        
        # Create multiple equipment
        for i in range(equipment_count):
            equipment_data = {
                'equipment_id': f'TEST-{i:03d}',
                'name': f'Test Equipment {i}',
                'type': equipment_type,
                'location': f'Location {i}',
                'status': 'active'
            }
            
            result = equipment_manager.register_equipment(equipment_data)
            assert result.success
            created_ids.append(equipment_data['equipment_id'])
        
        # List all equipment
        all_equipment = equipment_manager.list_all_equipment()
        
        # Property: All created equipment should be in the list
        listed_ids = [eq['equipment_id'] for eq in all_equipment]
        
        for created_id in created_ids:
            assert created_id in listed_ids, f"Equipment {created_id} not found in list"
        
        # Property: List should contain at least the equipment we created
        assert len(all_equipment) >= equipment_count
    
    finally:
        cleanup_test_db(db, db_path)