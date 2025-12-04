"""
Equipment Manager Service for Industrial Monitoring System
Handles business logic for equipment operations
"""

from typing import Dict, List, Optional
from repositories.equipment import EquipmentRepository


class ValidationError(Exception):
    """Raised when equipment data validation fails"""
    pass


class Result:
    """Result object for service operations"""
    
    def __init__(self, success: bool, data: Optional[Dict] = None, error_message: Optional[str] = None):
        self.success = success
        self.data = data
        self.error_message = error_message
        self.equipment_id = data.get('equipment_id') if data else None


class EquipmentManager:
    """
    Business logic for equipment operations
    Validates equipment data and coordinates with repository layer
    """
    
    # Required fields for equipment registration
    REQUIRED_FIELDS = ['equipment_id', 'name', 'type', 'location']
    
    # Valid equipment types
    VALID_TYPES = ['pump', 'motor', 'conveyor', 'sensor', 'compressor', 'valve', 'tank']
    
    def __init__(self, equipment_repo: EquipmentRepository):
        """
        Initialize EquipmentManager
        
        Args:
            equipment_repo: EquipmentRepository instance for data access
        """
        self.equipment_repo = equipment_repo
    
    def validate_equipment_data(self, data: Dict) -> bool:
        """
        Validate equipment data contains all required fields
        
        Args:
            data: Equipment data dictionary
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If validation fails with detailed error message
        """
        # Check for required fields
        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Validate equipment_id format (alphanumeric with hyphens/underscores)
        equipment_id = data['equipment_id']
        if not isinstance(equipment_id, str) or len(equipment_id) == 0:
            raise ValidationError("equipment_id must be a non-empty string")
        
        # Validate name
        if not isinstance(data['name'], str) or len(data['name']) == 0:
            raise ValidationError("name must be a non-empty string")
        
        # Validate type
        if data['type'] not in self.VALID_TYPES:
            raise ValidationError(
                f"Invalid equipment type '{data['type']}'. "
                f"Valid types: {', '.join(self.VALID_TYPES)}"
            )
        
        # Validate location
        if not isinstance(data['location'], str) or len(data['location']) == 0:
            raise ValidationError("location must be a non-empty string")
        
        return True
    
    def register_equipment(self, equipment_data: Dict) -> Result:
        """
        Register new equipment with validation
        
        Validates equipment data and creates equipment record.
        Checks for duplicate equipment_id.
        
        Args:
            equipment_data: Dictionary containing equipment fields
                - equipment_id: Unique equipment identifier
                - name: Equipment name
                - type: Equipment type
                - location: Equipment location
                - status: Equipment status (optional)
        
        Returns:
            Result object with success status and equipment data or error message
        """
        try:
            # Validate equipment data
            self.validate_equipment_data(equipment_data)
            
            # Check for duplicate equipment_id
            existing = self.equipment_repo.get_by_id(equipment_data['equipment_id'])
            if existing:
                return Result(
                    success=False,
                    error_message=f"Equipment with ID '{equipment_data['equipment_id']}' already exists"
                )
            
            # Create equipment record
            self.equipment_repo.create(equipment_data)
            
            # Retrieve created equipment
            created_equipment = self.equipment_repo.get_by_id(equipment_data['equipment_id'])
            
            return Result(
                success=True,
                data=created_equipment
            )
            
        except ValidationError as e:
            return Result(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            return Result(
                success=False,
                error_message=f"Failed to register equipment: {str(e)}"
            )
    
    def get_equipment_status(self, equipment_id: str) -> Dict:
        """
        Get equipment status and details
        
        Args:
            equipment_id: Unique equipment identifier
            
        Returns:
            Dictionary containing equipment details and status
            
        Raises:
            ValueError: If equipment not found
        """
        equipment = self.equipment_repo.get_by_id(equipment_id)
        
        if not equipment:
            raise ValueError(f"Equipment with ID '{equipment_id}' not found")
        
        return equipment
    
    def list_all_equipment(self) -> List[Dict]:
        """
        List all registered equipment
        
        Returns:
            List of equipment dictionaries
        """
        return self.equipment_repo.get_all()
    
    def update_equipment(self, equipment_id: str, data: Dict) -> Result:
        """
        Update equipment information
        
        Args:
            equipment_id: Unique equipment identifier
            data: Dictionary containing fields to update
            
        Returns:
            Result object with success status
        """
        try:
            # Check equipment exists
            existing = self.equipment_repo.get_by_id(equipment_id)
            if not existing:
                return Result(
                    success=False,
                    error_message=f"Equipment with ID '{equipment_id}' not found"
                )
            
            # Update equipment
            success = self.equipment_repo.update(equipment_id, data)
            
            if success:
                updated_equipment = self.equipment_repo.get_by_id(equipment_id)
                return Result(
                    success=True,
                    data=updated_equipment
                )
            else:
                return Result(
                    success=False,
                    error_message="Failed to update equipment"
                )
                
        except Exception as e:
            return Result(
                success=False,
                error_message=f"Failed to update equipment: {str(e)}"
            )
    
    def delete_equipment(self, equipment_id: str) -> Result:
        """
        Delete equipment
        
        Args:
            equipment_id: Unique equipment identifier
            
        Returns:
            Result object with success status
        """
        try:
            # Check equipment exists
            existing = self.equipment_repo.get_by_id(equipment_id)
            if not existing:
                return Result(
                    success=False,
                    error_message=f"Equipment with ID '{equipment_id}' not found"
                )
            
            # Delete equipment
            success = self.equipment_repo.delete(equipment_id)
            
            if success:
                return Result(success=True)
            else:
                return Result(
                    success=False,
                    error_message="Failed to delete equipment"
                )
                
        except Exception as e:
            return Result(
                success=False,
                error_message=f"Failed to delete equipment: {str(e)}"
            )
