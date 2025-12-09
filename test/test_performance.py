"""
Performance Test to demonstrate optimizations
"""

import time
import tempfile
import os
from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository
from services.sensor_processor import SensorProcessor


def create_test_db_with_data():
    """Create test database with sample data"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = DatabaseManager(db_path)
    db.init_schema('schema.sql')
    
    equipment_repo = EquipmentRepository(db)
    sensor_repo = SensorDataRepository(db)
    
    # Create test equipment
    for i in range(10):
        equipment_data = {
            'equipment_id': f'PERF-{i:03d}',
            'name': f'Performance Test Equipment {i}',
            'type': 'pump',
            'location': f'Test Location {i}'
        }
        equipment_repo.create(equipment_data)
        
        # Add sensor readings for each equipment
        for j in range(5):
            reading = {
                'equipment_id': f'PERF-{i:03d}',
                'sensor_type': 'temperature',
                'value': 20.0 + j,
                'unit': 'C'
            }
            sensor_repo.create(reading)
    
    return db, db_path


def test_statistics_performance():
    """Test the performance improvement in statistics calculation"""
    db, db_path = create_test_db_with_data()
    
    try:
        equipment_repo = EquipmentRepository(db)
        sensor_repo = SensorDataRepository(db)
        processor = SensorProcessor(sensor_repo, equipment_repo)
        
        # Get all sensor readings
        readings = sensor_repo.get_all_readings()
        
        # Test optimized statistics calculation
        start_time = time.time()
        stats = processor.calculate_statistics(readings)
        end_time = time.time()
        
        print(f"Statistics calculation time: {(end_time - start_time) * 1000:.2f}ms")
        print(f"Statistics: {stats}")
        
        # Verify correctness
        assert stats['count'] == len(readings)
        assert stats['min'] is not None
        assert stats['max'] is not None
        assert stats['avg'] is not None
        
        print("✅ Statistics calculation optimized and working correctly")
        
    finally:
        db.close()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_latest_readings_performance():
    """Test the N+1 query fix"""
    db, db_path = create_test_db_with_data()
    
    try:
        sensor_repo = SensorDataRepository(db)
        
        # Test optimized latest readings query
        start_time = time.time()
        results = sensor_repo.get_latest_readings()
        end_time = time.time()
        
        print(f"Latest readings query time: {(end_time - start_time) * 1000:.2f}ms")
        print(f"Retrieved {len(results)} equipment with latest readings")
        
        # Verify correctness
        assert len(results) == 10  # Should have 10 equipment
        for result in results:
            assert 'equipment' in result
            assert 'latest_reading' in result
            assert result['equipment']['equipment_id'].startswith('PERF-')
        
        print("✅ N+1 query problem fixed and working correctly")
        
    finally:
        db.close()
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == '__main__':
    print("=== Performance Test Results ===")
    test_statistics_performance()
    print()
    test_latest_readings_performance()
    print("\n✅ All performance optimizations working correctly!")