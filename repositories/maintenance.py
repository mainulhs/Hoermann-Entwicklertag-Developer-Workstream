"""
Maintenance Repository for Industrial Monitoring System
Handles maintenance record CRUD operations and overdue detection
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from database import DatabaseManager


class MaintenanceRepository:
    """Repository for maintenance record data access operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize MaintenanceRepository
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def create(self, maintenance: Dict) -> int:
        """
        Create a new maintenance record
        
        Args:
            maintenance: Dictionary containing maintenance fields
                - equipment_id: Equipment identifier
                - maintenance_type: Type of maintenance (preventive, corrective, inspection, etc.)
                - scheduled_date: Scheduled date for maintenance
                - description: Maintenance description
                - status: Maintenance status (optional, defaults to 'scheduled')
        
        Returns:
            ID of the newly created maintenance record
        """
        query = """
            INSERT INTO maintenance (equipment_id, maintenance_type, scheduled_date, description, status)
            VALUES (?, ?, ?, ?, ?)
        """
        status = maintenance.get('status', 'scheduled')
        params = (
            maintenance['equipment_id'],
            maintenance['maintenance_type'],
            maintenance['scheduled_date'],
            maintenance.get('description', ''),
            status
        )
        return self.db.execute_update(query, params)
    
    def update(self, maintenance_id: int, data: Dict) -> bool:
        """
        Update maintenance record
        
        Args:
            maintenance_id: Maintenance record ID
            data: Dictionary containing fields to update
                - completion_date: Date maintenance was completed
                - technician_notes: Notes from technician
                - status: Updated status
                - Any other allowed fields
        
        Returns:
            True if update successful, False otherwise
        """
        allowed_fields = [
            'maintenance_type', 'scheduled_date', 'completion_date',
            'description', 'technician_notes', 'status'
        ]
        update_fields = []
        params = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not update_fields:
            return False
        
        # Add maintenance_id to params for WHERE clause
        params.append(maintenance_id)
        
        query = f"UPDATE maintenance SET {', '.join(update_fields)} WHERE id = ?"
        rows_affected = self.db.execute_update(query, tuple(params))
        return rows_affected > 0
    
    def get_by_equipment(self, equipment_id: str, 
                        start_date: Optional[date] = None,
                        end_date: Optional[date] = None) -> List[Dict]:
        """
        Retrieve maintenance records for a specific equipment with optional date filtering
        
        Args:
            equipment_id: Equipment identifier
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of maintenance record dictionaries for the equipment
        """
        query = "SELECT * FROM maintenance WHERE equipment_id = ?"
        params = [equipment_id]
        
        if start_date:
            query += " AND scheduled_date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND scheduled_date <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY scheduled_date DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    def get_overdue(self) -> List[Dict]:
        """
        Retrieve all overdue maintenance records
        
        A maintenance record is considered overdue if:
        - scheduled_date is in the past
        - status is not 'completed'
        
        Returns:
            List of overdue maintenance record dictionaries
        """
        today = date.today().isoformat()
        query = """
            SELECT * FROM maintenance 
            WHERE scheduled_date < ? 
            AND status != 'completed'
            ORDER BY scheduled_date ASC
        """
        return self.db.execute_query(query, (today,))
    
    def get_by_id(self, maintenance_id: int) -> Optional[Dict]:
        """
        Retrieve a specific maintenance record by ID
        
        Args:
            maintenance_id: Maintenance record ID
            
        Returns:
            Maintenance record dictionary or None if not found
        """
        query = "SELECT * FROM maintenance WHERE id = ?"
        results = self.db.execute_query(query, (maintenance_id,))
        return results[0] if results else None
    
    def get_all(self, start_date: Optional[date] = None,
               end_date: Optional[date] = None) -> List[Dict]:
        """
        Retrieve all maintenance records with optional date filtering
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of maintenance record dictionaries
        """
        query = "SELECT * FROM maintenance WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND scheduled_date >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND scheduled_date <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY scheduled_date DESC"
        
        return self.db.execute_query(query, tuple(params))
    
    def get_by_status(self, status: str) -> List[Dict]:
        """
        Retrieve maintenance records by status
        
        Args:
            status: Maintenance status (scheduled, in_progress, completed, cancelled)
            
        Returns:
            List of maintenance record dictionaries with specified status
        """
        query = """
            SELECT * FROM maintenance 
            WHERE status = ? 
            ORDER BY scheduled_date DESC
        """
        return self.db.execute_query(query, (status,))
    
    def delete(self, maintenance_id: int) -> bool:
        """
        Delete a maintenance record
        
        Args:
            maintenance_id: Maintenance record ID
            
        Returns:
            True if deletion successful, False otherwise
        """
        query = "DELETE FROM maintenance WHERE id = ?"
        rows_affected = self.db.execute_update(query, (maintenance_id,))
        return rows_affected > 0
