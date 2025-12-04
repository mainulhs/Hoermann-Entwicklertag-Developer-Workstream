"""
Equipment Repository for Industrial Monitoring System
Handles CRUD operations for equipment data

SECURITY VULNERABILITY (INTENTIONAL):
- search() method uses string concatenation for SQL queries (SQL injection risk)
"""

from typing import List, Dict, Optional
from database import DatabaseManager


class EquipmentRepository:
    """
    Repository for equipment data access operations
    
    INTENTIONAL FLAW: SQL injection vulnerability in search() method
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize EquipmentRepository
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def create(self, equipment_data: Dict) -> int:
        """
        Create a new equipment record
        
        Args:
            equipment_data: Dictionary containing equipment fields
                - equipment_id: Unique equipment identifier
                - name: Equipment name
                - type: Equipment type
                - location: Equipment location
                - status: Equipment status (optional, defaults to 'active')
        
        Returns:
            ID of the newly created equipment record
            
        Raises:
            Exception: If equipment_id already exists or database error occurs
        """
        query = """
            INSERT INTO equipment (equipment_id, name, type, location, status)
            VALUES (?, ?, ?, ?, ?)
        """
        status = equipment_data.get('status', 'active')
        params = (
            equipment_data['equipment_id'],
            equipment_data['name'],
            equipment_data['type'],
            equipment_data['location'],
            status
        )
        return self.db.execute_update(query, params)
    
    def get_by_id(self, equipment_id: str) -> Optional[Dict]:
        """
        Retrieve equipment by equipment_id
        
        Args:
            equipment_id: Unique equipment identifier
            
        Returns:
            Equipment dictionary or None if not found
        """
        query = "SELECT * FROM equipment WHERE equipment_id = ?"
        results = self.db.execute_query(query, (equipment_id,))
        return results[0] if results else None
    
    def get_all(self) -> List[Dict]:
        """
        Retrieve all equipment records
        
        Returns:
            List of equipment dictionaries
        """
        query = "SELECT * FROM equipment ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def update(self, equipment_id: str, data: Dict) -> bool:
        """
        Update equipment record
        
        Args:
            equipment_id: Unique equipment identifier
            data: Dictionary containing fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        # Build update query dynamically based on provided fields
        allowed_fields = ['name', 'type', 'location', 'status']
        update_fields = []
        params = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not update_fields:
            return False
        
        # Add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # Add equipment_id to params for WHERE clause
        params.append(equipment_id)
        
        query = f"UPDATE equipment SET {', '.join(update_fields)} WHERE equipment_id = ?"
        rows_affected = self.db.execute_update(query, tuple(params))
        return rows_affected > 0
    
    def delete(self, equipment_id: str) -> bool:
        """
        Delete equipment record
        
        Args:
            equipment_id: Unique equipment identifier
            
        Returns:
            True if deletion successful, False otherwise
        """
        query = "DELETE FROM equipment WHERE equipment_id = ?"
        rows_affected = self.db.execute_update(query, (equipment_id,))
        return rows_affected > 0
    
    def search(self, query: str) -> List[Dict]:
        """
        Search equipment by name
        
        INTENTIONAL SECURITY VULNERABILITY: SQL Injection
        This method uses string concatenation instead of parameterized queries,
        making it vulnerable to SQL injection attacks.
        
        Example exploit: query = "' OR '1'='1"
        
        Args:
            query: Search query string
            
        Returns:
            List of matching equipment dictionaries
        """
        # VULNERABLE CODE - DO NOT USE IN PRODUCTION
        # Using string concatenation instead of parameterized query
        sql = f"SELECT * FROM equipment WHERE name LIKE '%{query}%'"
        return self.db.execute_query(sql, ())
