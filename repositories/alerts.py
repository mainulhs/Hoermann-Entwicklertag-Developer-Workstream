"""
Alert Repository for Industrial Monitoring System
Handles alert creation, querying, and acknowledgment
"""

from typing import List, Dict, Optional
from datetime import datetime
from database import DatabaseManager


class AlertRepository:
    """Repository for alert data access operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize AlertRepository
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
    
    def create(self, alert: Dict) -> int:
        """
        Create a new alert record
        
        Args:
            alert: Dictionary containing alert fields
                - equipment_id: Equipment identifier
                - alert_type: Type of alert (threshold_exceeded, equipment_failure, etc.)
                - severity: Alert severity (low, medium, high, critical)
                - message: Alert message description
                - status: Alert status (optional, defaults to 'active')
        
        Returns:
            ID of the newly created alert record
        """
        query = """
            INSERT INTO alerts (equipment_id, alert_type, severity, message, status)
            VALUES (?, ?, ?, ?, ?)
        """
        status = alert.get('status', 'active')
        params = (
            alert['equipment_id'],
            alert['alert_type'],
            alert['severity'],
            alert['message'],
            status
        )
        return self.db.execute_update(query, params)
    
    def get_active_alerts(self) -> List[Dict]:
        """
        Retrieve all active (unacknowledged) alerts, sorted by severity
        
        Severity order: critical > high > medium > low
        
        Returns:
            List of active alert dictionaries, sorted by severity (highest first)
        """
        query = """
            SELECT * FROM alerts 
            WHERE status = 'active' 
            ORDER BY 
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END,
                created_at DESC
        """
        return self.db.execute_query(query)
    
    def acknowledge(self, alert_id: int, user: str) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID to acknowledge
            user: Username of person acknowledging the alert
            
        Returns:
            True if acknowledgment successful, False otherwise
        """
        query = """
            UPDATE alerts 
            SET status = 'acknowledged',
                acknowledged_by = ?,
                acknowledged_at = ?
            WHERE id = ?
        """
        timestamp = datetime.now().isoformat()
        rows_affected = self.db.execute_update(query, (user, timestamp, alert_id))
        return rows_affected > 0
    
    def get_by_equipment(self, equipment_id: str) -> List[Dict]:
        """
        Retrieve all alerts for a specific equipment
        
        Args:
            equipment_id: Equipment identifier
            
        Returns:
            List of alert dictionaries for the equipment, ordered by creation time
        """
        query = """
            SELECT * FROM alerts 
            WHERE equipment_id = ? 
            ORDER BY created_at DESC
        """
        return self.db.execute_query(query, (equipment_id,))
    
    def get_by_id(self, alert_id: int) -> Optional[Dict]:
        """
        Retrieve a specific alert by ID
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Alert dictionary or None if not found
        """
        query = "SELECT * FROM alerts WHERE id = ?"
        results = self.db.execute_query(query, (alert_id,))
        return results[0] if results else None
    
    def get_all(self) -> List[Dict]:
        """
        Retrieve all alerts
        
        Returns:
            List of all alert dictionaries, ordered by creation time
        """
        query = "SELECT * FROM alerts ORDER BY created_at DESC"
        return self.db.execute_query(query)
    
    def get_by_severity(self, severity: str) -> List[Dict]:
        """
        Retrieve alerts by severity level
        
        Args:
            severity: Severity level (low, medium, high, critical)
            
        Returns:
            List of alert dictionaries with specified severity
        """
        query = """
            SELECT * FROM alerts 
            WHERE severity = ? 
            ORDER BY created_at DESC
        """
        return self.db.execute_query(query, (severity,))
    
    def get_by_status(self, status: str) -> List[Dict]:
        """
        Retrieve alerts by status
        
        Args:
            status: Alert status (active, acknowledged)
            
        Returns:
            List of alert dictionaries with specified status
        """
        query = """
            SELECT * FROM alerts 
            WHERE status = ? 
            ORDER BY created_at DESC
        """
        return self.db.execute_query(query, (status,))
