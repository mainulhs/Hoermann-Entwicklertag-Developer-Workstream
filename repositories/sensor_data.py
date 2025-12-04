"""
Sensor Data Repository for Industrial Monitoring System
Handles storage and retrieval of sensor readings

PERFORMANCE ISSUE (INTENTIONAL):
- get_latest_readings() method has N+1 query problem
"""

from typing import List, Dict, Optional
from datetime import datetime
from database import DatabaseManager


class SensorDataRepository:
    """
    Repository for sensor reading data access operations
    
    INTENTIONAL FLAW: N+1 query problem in get_latest_readings() method
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize SensorDataRepository
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def create(self, reading: Dict) -> int:
        """
        Store a new sensor reading
        
        Args:
            reading: Dictionary containing sensor reading fields
                - equipment_id: Equipment identifier
                - sensor_type: Type of sensor (temperature, pressure, vibration, etc.)
                - value: Sensor reading value
                - unit: Unit of measurement (optional)
                - timestamp: Reading timestamp (optional, defaults to current time)
        
        Returns:
            ID of the newly created sensor reading record
        """
        query = """
            INSERT INTO sensor_readings (equipment_id, sensor_type, value, unit, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        timestamp = reading.get('timestamp', datetime.now().isoformat())
        unit = reading.get('unit', None)
        
        params = (
            reading['equipment_id'],
            reading['sensor_type'],
            reading['value'],
            unit,
            timestamp
        )
        return self.db.execute_update(query, params)
    
    def get_by_equipment(self, equipment_id: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve sensor readings for a specific equipment
        
        Args:
            equipment_id: Equipment identifier
            limit: Maximum number of readings to return
            
        Returns:
            List of sensor reading dictionaries, ordered by timestamp descending
        """
        query = """
            SELECT * FROM sensor_readings 
            WHERE equipment_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        return self.db.execute_query(query, (equipment_id, limit))
    
    def get_by_date_range(self, start: datetime, end: datetime, 
                          equipment_id: Optional[str] = None,
                          sensor_type: Optional[str] = None) -> List[Dict]:
        """
        Retrieve sensor readings within a date range with optional filters
        
        Args:
            start: Start datetime for range
            end: End datetime for range
            equipment_id: Optional equipment filter
            sensor_type: Optional sensor type filter
            
        Returns:
            List of sensor reading dictionaries within the date range
        """
        query = "SELECT * FROM sensor_readings WHERE timestamp >= ? AND timestamp <= ?"
        params = [start.isoformat(), end.isoformat()]
        
        if equipment_id:
            query += " AND equipment_id = ?"
            params.append(equipment_id)
        
        if sensor_type:
            query += " AND sensor_type = ?"
            params.append(sensor_type)
        
        query += " ORDER BY timestamp DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    def get_latest_for_equipment(self, equipment_id: str) -> Optional[Dict]:
        """
        Get the most recent sensor reading for a specific equipment
        
        Args:
            equipment_id: Equipment identifier
            
        Returns:
            Most recent sensor reading dictionary or None if no readings exist
        """
        query = """
            SELECT * FROM sensor_readings 
            WHERE equipment_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        results = self.db.execute_query(query, (equipment_id,))
        return results[0] if results else None
    
    def get_latest_readings(self) -> List[Dict]:
        """
        Get the latest sensor reading for each equipment
        
        INTENTIONAL PERFORMANCE ISSUE: N+1 Query Problem
        This method first queries all equipment, then makes a separate query
        for each equipment to get its latest reading. This results in N+1 queries
        where N is the number of equipment items.
        
        A better approach would be to use a single query with window functions
        or a subquery to get all latest readings at once.
        
        Returns:
            List of dictionaries containing equipment and their latest readings
        """
        # INEFFICIENT CODE - DO NOT USE IN PRODUCTION
        # First query: Get all equipment (1 query)
        equipment_query = "SELECT * FROM equipment"
        equipment_list = self.db.execute_query(equipment_query)
        
        results = []
        # N queries: One query per equipment item
        for equipment in equipment_list:
            reading = self.get_latest_for_equipment(equipment['equipment_id'])
            results.append({
                'equipment': equipment,
                'latest_reading': reading
            })
        
        return results
    
    def get_all_readings(self) -> List[Dict]:
        """
        Retrieve all sensor readings (WARNING: Can be very large)
        
        Returns:
            List of all sensor reading dictionaries
        """
        query = "SELECT * FROM sensor_readings ORDER BY timestamp DESC"
        return self.db.execute_query(query)
    
    def get_readings_by_filters(self, equipment_id: Optional[str] = None,
                                sensor_type: Optional[str] = None,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Retrieve sensor readings with multiple optional filters
        
        Args:
            equipment_id: Optional equipment filter
            sensor_type: Optional sensor type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of sensor reading dictionaries matching all specified filters
        """
        query = "SELECT * FROM sensor_readings WHERE 1=1"
        params = []
        
        if equipment_id:
            query += " AND equipment_id = ?"
            params.append(equipment_id)
        
        if sensor_type:
            query += " AND sensor_type = ?"
            params.append(sensor_type)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        return self.db.execute_query(query, tuple(params))
