"""
Property-based tests for database persistence
Tests that equipment data persists across database restarts
"""

import os
import uuid
from hypothesis import given, strategies as st, settings
from database import DatabaseManager


# Strategy for generating valid equipment data
equipment_strategy = st.fixed_dictionaries({
    'equipment_id': st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
        min_size=1,
        max_size=50
    ).filter(lambda x: x.strip() and not x.startswith('-') and not x.startswith('_')),
    'name': st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    'type': st.sampled_from(['pump', 'motor', 'conveyor', 'sensor', 'compressor', 'valve']),
    'location': st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
})


# Feature: industrial-monitoring-system, Property 4: Equipment persistence across restarts
@given(equipment=equipment_strategy)
@settings(max_examples=100)
def test_equipment_persistence_across_restarts(equipment):
    """
    Property 4: Equipment persistence across restarts
    
    For any equipment stored in the database, after a system restart,
    querying by equipment_id should return the same equipment data.
    
    Validates: Requirements 1.4
    """
    # Generate unique test database path for this test run
    test_db_path = f"test_persistence_{uuid.uuid4().hex}.db"
    
    # Phase 1: Store equipment and close connection (simulating shutdown)
    db1 = DatabaseManager(test_db_path)
    try:
        # Initialize schema
        db1.init_schema()
        
        # Insert equipment
        insert_query = """
            INSERT INTO equipment (equipment_id, name, type, location, status)
            VALUES (?, ?, ?, ?, 'active')
        """
        db1.execute_update(
            insert_query,
            (equipment['equipment_id'], equipment['name'], equipment['type'], equipment['location'])
        )
    finally:
        # Close connection (simulating system shutdown)
        db1.close()
    
    # Phase 2: Reopen connection (simulating system restart) and verify data
    db2 = DatabaseManager(test_db_path)
    try:
        # Query equipment by equipment_id
        select_query = """
            SELECT equipment_id, name, type, location, status
            FROM equipment
            WHERE equipment_id = ?
        """
        results = db2.execute_query(select_query, (equipment['equipment_id'],))
        
        # Verify equipment was persisted
        assert len(results) == 1, f"Expected 1 equipment record, found {len(results)}"
        
        retrieved = results[0]
        assert retrieved['equipment_id'] == equipment['equipment_id'], \
            f"Equipment ID mismatch: expected {equipment['equipment_id']}, got {retrieved['equipment_id']}"
        assert retrieved['name'] == equipment['name'], \
            f"Name mismatch: expected {equipment['name']}, got {retrieved['name']}"
        assert retrieved['type'] == equipment['type'], \
            f"Type mismatch: expected {equipment['type']}, got {retrieved['type']}"
        assert retrieved['location'] == equipment['location'], \
            f"Location mismatch: expected {equipment['location']}, got {retrieved['location']}"
        assert retrieved['status'] == 'active', \
            f"Status should be 'active', got {retrieved['status']}"
    finally:
        db2.close()
        # Cleanup test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
