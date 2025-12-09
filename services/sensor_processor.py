"""
Sensor Processor Service for Industrial Monitoring System
Handles sensor reading recording and threshold checking

PERFORMANCE ISSUE (INTENTIONAL):
- calculate_statistics() uses inefficient multi-pass calculation
"""

from typing import Dict, List, Optional
from datetime import datetime
from repositories.sensor_data import SensorDataRepository
from repositories.equipment import EquipmentRepository


class ValidationError(Exception):
    """Raised when sensor reading validation fails"""
    pass


class Result:
    """Result object for service operations"""
    
    def __init__(self, success: bool, data: Optional[Dict] = None, error_message: Optional[str] = None):
        self.success = success
        self.data = data
        self.error_message = error_message


class Alert:
    """Alert object for threshold violations"""
    
    def __init__(self, equipment_id: str, sensor_type: str, value: float, 
                 threshold: float, alert_type: str, severity: str, message: str):
        self.equipment_id = equipment_id
        self.sensor_type = sensor_type
        self.value = value
        self.threshold = threshold
        self.alert_type = alert_type
        self.severity = severity
        self.message = message


class SensorProcessor:
    """
    Business logic for sensor reading processing
    Handles recording, validation, and threshold checking
    
    INTENTIONAL FLAW: Inefficient statistics calculation
    """
    
    # Required fields for sensor readings
    REQUIRED_FIELDS = ['equipment_id', 'sensor_type', 'value']
    
    # Valid sensor types
    VALID_SENSOR_TYPES = [
        'temperature', 'pressure', 'vibration', 'flow_rate', 
        'rpm', 'voltage', 'current', 'humidity'
    ]
    
    # Default thresholds for sensor types
    DEFAULT_THRESHOLDS = {
        'temperature': {'max': 80.0, 'min': -10.0},
        'pressure': {'max': 150.0, 'min': 0.0},
        'vibration': {'max': 10.0, 'min': 0.0},
        'flow_rate': {'max': 1000.0, 'min': 0.0},
        'rpm': {'max': 5000.0, 'min': 0.0},
        'voltage': {'max': 250.0, 'min': 0.0},
        'current': {'max': 100.0, 'min': 0.0},
        'humidity': {'max': 100.0, 'min': 0.0}
    }
    
    def __init__(self, sensor_repo: SensorDataRepository, 
                 equipment_repo: EquipmentRepository,
                 thresholds: Optional[Dict] = None):
        """
        Initialize SensorProcessor
        
        Args:
            sensor_repo: SensorDataRepository instance for data access
            equipment_repo: EquipmentRepository instance for equipment validation
            thresholds: Optional custom threshold configuration
        """
        self.sensor_repo = sensor_repo
        self.equipment_repo = equipment_repo
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
    
    def validate_reading(self, reading: Dict) -> bool:
        """
        Validate sensor reading data
        
        Args:
            reading: Sensor reading dictionary
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails with detailed error message
        """
        # Check for required fields
        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            if field not in reading or reading[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Validate equipment exists
        equipment = self.equipment_repo.get_by_id(reading['equipment_id'])
        if not equipment:
            raise ValidationError(
                f"Equipment with ID '{reading['equipment_id']}' not found"
            )
        
        # Validate sensor_type
        if reading['sensor_type'] not in self.VALID_SENSOR_TYPES:
            raise ValidationError(
                f"Invalid sensor type '{reading['sensor_type']}'. "
                f"Valid types: {', '.join(self.VALID_SENSOR_TYPES)}"
            )
        
        # Validate value is numeric
        try:
            float(reading['value'])
        except (ValueError, TypeError):
            raise ValidationError("Sensor value must be numeric")
        
        return True
    
    def record_reading(self, reading: Dict) -> Result:
        """
        Record a sensor reading with validation
        
        Validates reading data, stores it, and checks thresholds.
        
        Args:
            reading: Dictionary containing sensor reading fields
                - equipment_id: Equipment identifier
                - sensor_type: Type of sensor
                - value: Sensor reading value
                - unit: Unit of measurement (optional)
                - timestamp: Reading timestamp (optional)
        
        Returns:
            Result object with success status and reading data or error message
        """
        try:
            # Validate reading
            self.validate_reading(reading)
            
            # Add timestamp if not provided
            if 'timestamp' not in reading:
                reading['timestamp'] = datetime.now().isoformat()
            
            # Store reading
            reading_id = self.sensor_repo.create(reading)
            
            # Check thresholds
            alert = self.check_thresholds(reading)
            
            return Result(
                success=True,
                data={
                    'reading_id': reading_id,
                    'alert': alert.__dict__ if alert else None
                }
            )
            
        except ValidationError as e:
            return Result(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return Result(
                success=False,
                error_message=f"Failed to record reading: {str(e)}"
            )
    
    def check_thresholds(self, reading: Dict) -> Optional[Alert]:
        """
        Check if sensor reading exceeds configured thresholds
        
        Args:
            reading: Sensor reading dictionary
            
        Returns:
            Alert object if threshold exceeded, None otherwise
        """
        sensor_type = reading['sensor_type']
        value = float(reading['value'])
        
        # Get thresholds for this sensor type
        if sensor_type not in self.thresholds:
            return None
        
        threshold_config = self.thresholds[sensor_type]
        
        # Check maximum threshold
        if 'max' in threshold_config and value > threshold_config['max']:
            severity = self._determine_severity(value, threshold_config['max'], 'max')
            return Alert(
                equipment_id=reading['equipment_id'],
                sensor_type=sensor_type,
                value=value,
                threshold=threshold_config['max'],
                alert_type='threshold_exceeded',
                severity=severity,
                message=f"{sensor_type} reading {value} exceeds maximum threshold {threshold_config['max']}"
            )
        
        # Check minimum threshold
        if 'min' in threshold_config and value < threshold_config['min']:
            severity = self._determine_severity(value, threshold_config['min'], 'min')
            return Alert(
                equipment_id=reading['equipment_id'],
                sensor_type=sensor_type,
                value=value,
                threshold=threshold_config['min'],
                alert_type='threshold_exceeded',
                severity=severity,
                message=f"{sensor_type} reading {value} below minimum threshold {threshold_config['min']}"
            )
        
        return None
    
    def _determine_severity(self, value: float, threshold: float, threshold_type: str) -> str:
        """
        Determine alert severity based on how much threshold is exceeded
        
        Args:
            value: Actual sensor value
            threshold: Threshold value
            threshold_type: 'max' or 'min'
            
        Returns:
            Severity level: 'low', 'medium', 'high', or 'critical'
        """
        if threshold_type == 'max':
            percent_over = ((value - threshold) / threshold) * 100
        else:  # min
            percent_over = ((threshold - value) / threshold) * 100
        
        if percent_over > 50:
            return 'critical'
        elif percent_over > 25:
            return 'high'
        elif percent_over > 10:
            return 'medium'
        else:
            return 'low'
    
    def get_equipment_history(self, equipment_id: str, days: int = 7) -> List[Dict]:
        """
        Get sensor reading history for equipment
        
        Args:
            equipment_id: Equipment identifier
            days: Number of days of history to retrieve
            
        Returns:
            List of sensor reading dictionaries
        """
        # Calculate date range
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.sensor_repo.get_by_date_range(
            start=start_date,
            end=end_date,
            equipment_id=equipment_id
        )
    
    def calculate_statistics(self, readings: List[Dict]) -> Dict:
        """
        Calculate statistics for sensor readings
        
        OPTIMIZED: Single-pass calculation for all statistics
        
        Args:
            readings: List of sensor reading dictionaries
            
        Returns:
            Dictionary containing min, max, avg, count statistics
        """
        if not readings:
            return {
                'min': None,
                'max': None,
                'avg': None,
                'count': 0
            }
        
        # Single pass calculation - much more efficient
        count = len(readings)
        total = 0.0
        min_val = float('inf')
        max_val = float('-inf')
        
        for reading in readings:
            value = float(reading['value'])
            total += value
            min_val = min(min_val, value)
            max_val = max(max_val, value)
        
        return {
            'min': min_val,
            'max': max_val,
            'avg': total / count,
            'count': count
        }
