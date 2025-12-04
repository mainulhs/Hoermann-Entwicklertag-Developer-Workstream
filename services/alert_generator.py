"""
Alert Generator Service for Industrial Monitoring System
Handles alert generation, querying, and acknowledgment
"""

from typing import Dict, List, Optional
from repositories.alerts import AlertRepository
from repositories.equipment import EquipmentRepository


class ValidationError(Exception):
    """Raised when alert data validation fails"""
    pass


class Result:
    """Result object for service operations"""
    
    def __init__(self, success: bool, data: Optional[Dict] = None, error_message: Optional[str] = None):
        self.success = success
        self.data = data
        self.error_message = error_message


class AlertGenerator:
    """
    Business logic for alert generation and management
    Handles alert creation, querying, and acknowledgment
    """
    
    # Valid alert types
    VALID_ALERT_TYPES = [
        'threshold_exceeded',
        'equipment_failure',
        'maintenance_due',
        'communication_error',
        'sensor_malfunction'
    ]
    
    # Valid severity levels
    VALID_SEVERITIES = ['low', 'medium', 'high', 'critical']
    
    def __init__(self, alert_repo: AlertRepository, equipment_repo: EquipmentRepository):
        """
        Initialize AlertGenerator
        
        Args:
            alert_repo: AlertRepository instance for data access
            equipment_repo: EquipmentRepository instance for equipment validation
        """
        self.alert_repo = alert_repo
        self.equipment_repo = equipment_repo
    
    def validate_alert_data(self, equipment_id: str, alert_type: str, 
                           severity: str, message: str) -> bool:
        """
        Validate alert data
        
        Args:
            equipment_id: Equipment identifier
            alert_type: Type of alert
            severity: Alert severity level
            message: Alert message
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails with detailed error message
        """
        # Validate equipment exists
        equipment = self.equipment_repo.get_by_id(equipment_id)
        if not equipment:
            raise ValidationError(
                f"Equipment with ID '{equipment_id}' not found"
            )
        
        # Validate alert_type
        if alert_type not in self.VALID_ALERT_TYPES:
            raise ValidationError(
                f"Invalid alert type '{alert_type}'. "
                f"Valid types: {', '.join(self.VALID_ALERT_TYPES)}"
            )
        
        # Validate severity
        if severity not in self.VALID_SEVERITIES:
            raise ValidationError(
                f"Invalid severity '{severity}'. "
                f"Valid severities: {', '.join(self.VALID_SEVERITIES)}"
            )
        
        # Validate message
        if not message or not isinstance(message, str):
            raise ValidationError("Alert message must be a non-empty string")
        
        return True
    
    def generate_alert(self, equipment_id: str, alert_type: str, 
                      severity: str, message: str) -> int:
        """
        Generate a new alert
        
        Validates alert data and creates alert record.
        
        Args:
            equipment_id: Equipment identifier
            alert_type: Type of alert (threshold_exceeded, equipment_failure, etc.)
            severity: Alert severity (low, medium, high, critical)
            message: Alert message description
            
        Returns:
            ID of the newly created alert
            
        Raises:
            ValidationError: If validation fails
            Exception: If alert creation fails
        """
        # Validate alert data
        self.validate_alert_data(equipment_id, alert_type, severity, message)
        
        # Create alert
        alert_data = {
            'equipment_id': equipment_id,
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'status': 'active'
        }
        
        alert_id = self.alert_repo.create(alert_data)
        return alert_id
    
    def get_active_alerts(self) -> List[Dict]:
        """
        Get all active (unacknowledged) alerts
        
        Returns alerts sorted by severity (highest first), then by creation time.
        
        Returns:
            List of active alert dictionaries
        """
        return self.alert_repo.get_active_alerts()
    
    def acknowledge_alert(self, alert_id: int, user: str) -> Result:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID to acknowledge
            user: Username of person acknowledging the alert
            
        Returns:
            Result object with success status
        """
        try:
            # Validate alert exists
            alert = self.alert_repo.get_by_id(alert_id)
            if not alert:
                return Result(
                    success=False,
                    error_message=f"Alert with ID {alert_id} not found"
                )
            
            # Check if already acknowledged
            if alert['status'] == 'acknowledged':
                return Result(
                    success=False,
                    error_message=f"Alert {alert_id} is already acknowledged"
                )
            
            # Acknowledge alert
            success = self.alert_repo.acknowledge(alert_id, user)
            
            if success:
                # Retrieve updated alert
                updated_alert = self.alert_repo.get_by_id(alert_id)
                return Result(
                    success=True,
                    data=updated_alert
                )
            else:
                return Result(
                    success=False,
                    error_message="Failed to acknowledge alert"
                )
                
        except Exception as e:
            return Result(
                success=False,
                error_message=f"Failed to acknowledge alert: {str(e)}"
            )
    
    def get_equipment_alerts(self, equipment_id: str) -> List[Dict]:
        """
        Get all alerts for a specific equipment
        
        Args:
            equipment_id: Equipment identifier
            
        Returns:
            List of alert dictionaries for the equipment
        """
        return self.alert_repo.get_by_equipment(equipment_id)
    
    def get_alerts_by_severity(self, severity: str) -> List[Dict]:
        """
        Get alerts by severity level
        
        Args:
            severity: Severity level (low, medium, high, critical)
            
        Returns:
            List of alert dictionaries with specified severity
            
        Raises:
            ValidationError: If severity is invalid
        """
        if severity not in self.VALID_SEVERITIES:
            raise ValidationError(
                f"Invalid severity '{severity}'. "
                f"Valid severities: {', '.join(self.VALID_SEVERITIES)}"
            )
        
        return self.alert_repo.get_by_severity(severity)
    
    def get_all_alerts(self) -> List[Dict]:
        """
        Get all alerts (active and acknowledged)
        
        Returns:
            List of all alert dictionaries
        """
        return self.alert_repo.get_all()
