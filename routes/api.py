"""
REST API Routes for Industrial Monitoring System
Provides RESTful HTTP endpoints for all core operations

INTENTIONAL FLAWS:
- DELETE /api/equipment/<id> missing authentication check
- Sensor readings endpoint returns all data without pagination
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Any, Optional
from services.equipment_manager import EquipmentManager, ValidationError
from services.sensor_processor import SensorProcessor
from services.alert_generator import AlertGenerator
from services.auth_service import AuthService, AuthenticationError
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository
from repositories.alerts import AlertRepository
from repositories.maintenance import MaintenanceRepository
from repositories.users import UserRepository
from database import DatabaseManager


# Create Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global service instances (will be initialized by app)
equipment_manager: Optional[EquipmentManager] = None
sensor_processor: Optional[SensorProcessor] = None
alert_generator: Optional[AlertGenerator] = None
auth_service: Optional[AuthService] = None
maintenance_repo: Optional[MaintenanceRepository] = None


def init_api_services(db_manager: DatabaseManager):
    """
    Initialize API service instances
    
    Args:
        db_manager: DatabaseManager instance
    """
    global equipment_manager, sensor_processor, alert_generator, auth_service, maintenance_repo
    
    # Initialize repositories
    equipment_repo = EquipmentRepository(db_manager)
    sensor_repo = SensorDataRepository(db_manager)
    alert_repo = AlertRepository(db_manager)
    user_repo = UserRepository(db_manager)
    maintenance_repo = MaintenanceRepository(db_manager)
    
    # Initialize services
    equipment_manager = EquipmentManager(equipment_repo)
    sensor_processor = SensorProcessor(sensor_repo, equipment_repo)
    alert_generator = AlertGenerator(alert_repo, equipment_repo)
    auth_service = AuthService(user_repo)


def error_response(message: str, status_code: int) -> tuple:
    """
    Create standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return jsonify({
        'error': 'Error',
        'message': message,
        'timestamp': datetime.now().isoformat()
    }), status_code


def success_response(data: Any, status_code: int = 200) -> tuple:
    """
    Create standardized success response
    
    Args:
        data: Response data
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return jsonify(data), status_code


def get_auth_token() -> Optional[str]:
    """
    Extract authentication token from request headers
    
    Returns:
        Token string or None if not present
    """
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return None


def require_auth():
    """
    Require valid authentication for endpoint
    
    Returns:
        User info dictionary
        
    Raises:
        AuthenticationError: If authentication fails
    """
    token = get_auth_token()
    if not token:
        raise AuthenticationError("Authentication token required")
    
    user_info = auth_service.validate_token(token)
    if not user_info:
        raise AuthenticationError("Invalid or expired authentication token")
    
    return user_info


# ============================================================================
# Equipment Endpoints
# ============================================================================

@api_bp.route('/equipment', methods=['POST'])
def register_equipment():
    """
    Register new equipment
    
    POST /api/equipment
    
    Request body:
        {
            "equipment_id": "PUMP-001",
            "name": "Main Water Pump",
            "type": "pump",
            "location": "Building A"
        }
    
    Returns:
        201: Equipment registered successfully
        400: Validation error
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        result = equipment_manager.register_equipment(data)
        
        if result.success:
            return success_response(result.data, 201)
        else:
            return error_response(result.error_message, 400)
            
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/equipment', methods=['GET'])
def list_equipment():
    """
    List all equipment
    
    GET /api/equipment
    
    Returns:
        200: List of equipment
        500: Server error
    """
    try:
        equipment_list = equipment_manager.list_all_equipment()
        return success_response({'equipment': equipment_list})
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/equipment/<equipment_id>', methods=['GET'])
def get_equipment(equipment_id: str):
    """
    Get equipment details
    
    GET /api/equipment/<id>
    
    Returns:
        200: Equipment details
        404: Equipment not found
        500: Server error
    """
    try:
        equipment = equipment_manager.get_equipment_status(equipment_id)
        return success_response(equipment)
        
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/equipment/<equipment_id>', methods=['PUT'])
def update_equipment(equipment_id: str):
    """
    Update equipment
    
    PUT /api/equipment/<id>
    
    Request body:
        {
            "name": "Updated Name",
            "status": "maintenance"
        }
    
    Returns:
        200: Equipment updated successfully
        400: Validation error
        404: Equipment not found
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        result = equipment_manager.update_equipment(equipment_id, data)
        
        if result.success:
            return success_response(result.data)
        else:
            # Check if it's a not found error
            if "not found" in result.error_message.lower():
                return error_response(result.error_message, 404)
            return error_response(result.error_message, 400)
            
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/equipment/<equipment_id>', methods=['DELETE'])
def delete_equipment(equipment_id: str):
    """
    Delete equipment
    
    DELETE /api/equipment/<id>
    
    INTENTIONAL SECURITY FLAW: Missing authentication check
    Anyone can delete equipment without authentication!
    
    Returns:
        200: Equipment deleted successfully
        404: Equipment not found
        500: Server error
    """
    # VULNERABLE CODE - Missing authentication check
    # Should have: require_auth()
    
    try:
        result = equipment_manager.delete_equipment(equipment_id)
        
        if result.success:
            return success_response({'message': 'Equipment deleted successfully'})
        else:
            if "not found" in result.error_message.lower():
                return error_response(result.error_message, 404)
            return error_response(result.error_message, 400)
            
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


# ============================================================================
# Sensor Endpoints
# ============================================================================

@api_bp.route('/sensors/readings', methods=['POST'])
def record_sensor_reading():
    """
    Record a sensor reading
    
    POST /api/sensors/readings
    
    Request body:
        {
            "equipment_id": "PUMP-001",
            "sensor_type": "temperature",
            "value": 75.5,
            "unit": "celsius"
        }
    
    Returns:
        201: Reading recorded successfully
        400: Validation error
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        result = sensor_processor.record_reading(data)
        
        if result.success:
            # If alert was generated, also create it in the database
            if result.data.get('alert'):
                alert_data = result.data['alert']
                alert_generator.generate_alert(
                    alert_data['equipment_id'],
                    alert_data['alert_type'],
                    alert_data['severity'],
                    alert_data['message']
                )
            
            return success_response(result.data, 201)
        else:
            return error_response(result.error_message, 400)
            
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/sensors/readings', methods=['GET'])
def query_sensor_readings():
    """
    Query sensor readings with filters
    
    GET /api/sensors/readings?equipment_id=PUMP-001&sensor_type=temperature&start_date=2024-01-01&end_date=2024-12-31
    
    Query parameters:
        - equipment_id: Filter by equipment ID (optional)
        - sensor_type: Filter by sensor type (optional)
        - start_date: Start date for range (optional, ISO format)
        - end_date: End date for range (optional, ISO format)
    
    INTENTIONAL PERFORMANCE ISSUE: Returns all data without pagination
    This can result in very large responses that slow down the API.
    
    Returns:
        200: List of sensor readings
        400: Invalid parameters
        500: Server error
    """
    try:
        # Extract query parameters
        equipment_id = request.args.get('equipment_id')
        sensor_type = request.args.get('sensor_type')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates if provided
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return error_response("Invalid start_date format. Use ISO format (YYYY-MM-DD)", 400)
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return error_response("Invalid end_date format. Use ISO format (YYYY-MM-DD)", 400)
        
        # Get sensor repository from sensor processor
        sensor_repo = sensor_processor.sensor_repo
        
        # Query readings with filters
        # PERFORMANCE ISSUE: No pagination - returns ALL matching readings
        readings = sensor_repo.get_readings_by_filters(
            equipment_id=equipment_id,
            sensor_type=sensor_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return success_response({'readings': readings, 'count': len(readings)})
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/equipment/<equipment_id>/sensors', methods=['GET'])
def get_equipment_sensor_history(equipment_id: str):
    """
    Get sensor reading history for equipment
    
    GET /api/equipment/<id>/sensors?days=7
    
    Query parameters:
        - days: Number of days of history (optional, default 7)
    
    INTENTIONAL PERFORMANCE ISSUE: Returns all data without pagination
    
    Returns:
        200: List of sensor readings for equipment
        400: Invalid parameters
        404: Equipment not found
        500: Server error
    """
    try:
        # Get days parameter
        days = request.args.get('days', 7, type=int)
        
        if days < 1:
            return error_response("days parameter must be positive", 400)
        
        # Check if equipment exists
        try:
            equipment_manager.get_equipment_status(equipment_id)
        except ValueError:
            return error_response(f"Equipment with ID '{equipment_id}' not found", 404)
        
        # Get sensor history (no pagination - PERFORMANCE ISSUE)
        readings = sensor_processor.get_equipment_history(equipment_id, days)
        
        return success_response({
            'equipment_id': equipment_id,
            'readings': readings,
            'count': len(readings),
            'days': days
        })
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


# ============================================================================
# Alert Endpoints
# ============================================================================

@api_bp.route('/alerts', methods=['GET'])
def get_active_alerts():
    """
    Get all active alerts
    
    GET /api/alerts
    
    Returns:
        200: List of active alerts sorted by severity
        500: Server error
    """
    try:
        alerts = alert_generator.get_active_alerts()
        return success_response({'alerts': alerts, 'count': len(alerts)})
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/alerts/<int:alert_id>/ack', methods=['POST'])
def acknowledge_alert(alert_id: int):
    """
    Acknowledge an alert
    
    POST /api/alerts/<id>/ack
    
    Request body:
        {
            "user": "operator1"
        }
    
    Returns:
        200: Alert acknowledged successfully
        400: Validation error
        404: Alert not found
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data or 'user' not in data:
            return error_response("Request body must include 'user' field", 400)
        
        user = data['user']
        result = alert_generator.acknowledge_alert(alert_id, user)
        
        if result.success:
            return success_response(result.data)
        else:
            if "not found" in result.error_message.lower():
                return error_response(result.error_message, 404)
            return error_response(result.error_message, 400)
            
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/equipment/<equipment_id>/alerts', methods=['GET'])
def get_equipment_alerts(equipment_id: str):
    """
    Get all alerts for a specific equipment
    
    GET /api/equipment/<id>/alerts
    
    Returns:
        200: List of alerts for equipment
        404: Equipment not found
        500: Server error
    """
    try:
        # Check if equipment exists
        try:
            equipment_manager.get_equipment_status(equipment_id)
        except ValueError:
            return error_response(f"Equipment with ID '{equipment_id}' not found", 404)
        
        alerts = alert_generator.get_equipment_alerts(equipment_id)
        
        return success_response({
            'equipment_id': equipment_id,
            'alerts': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


# ============================================================================
# Maintenance Endpoints
# ============================================================================

@api_bp.route('/maintenance', methods=['POST'])
def create_maintenance_record():
    """
    Create a maintenance record
    
    POST /api/maintenance
    
    Request body:
        {
            "equipment_id": "PUMP-001",
            "maintenance_type": "preventive",
            "scheduled_date": "2024-12-15",
            "description": "Routine maintenance check"
        }
    
    Returns:
        201: Maintenance record created successfully
        400: Validation error
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        # Validate required fields
        required_fields = ['equipment_id', 'maintenance_type', 'scheduled_date']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            return error_response(
                f"Missing required fields: {', '.join(missing_fields)}", 
                400
            )
        
        # Check if equipment exists
        try:
            equipment_manager.get_equipment_status(data['equipment_id'])
        except ValueError as e:
            return error_response(str(e), 404)
        
        # Create maintenance record
        maintenance_id = maintenance_repo.create(data)
        
        # Retrieve created record
        created_record = maintenance_repo.get_by_id(maintenance_id)
        
        return success_response(created_record, 201)
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/maintenance', methods=['GET'])
def list_maintenance_records():
    """
    List maintenance records with optional filters
    
    GET /api/maintenance?equipment_id=PUMP-001&start_date=2024-01-01&end_date=2024-12-31
    
    Query parameters:
        - equipment_id: Filter by equipment ID (optional)
        - start_date: Start date for range (optional, ISO format)
        - end_date: End date for range (optional, ISO format)
    
    Returns:
        200: List of maintenance records
        400: Invalid parameters
        500: Server error
    """
    try:
        equipment_id = request.args.get('equipment_id')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates if provided
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str).date()
            except ValueError:
                return error_response("Invalid start_date format. Use ISO format (YYYY-MM-DD)", 400)
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str).date()
            except ValueError:
                return error_response("Invalid end_date format. Use ISO format (YYYY-MM-DD)", 400)
        
        # Query maintenance records
        if equipment_id:
            records = maintenance_repo.get_by_equipment(equipment_id, start_date, end_date)
        else:
            records = maintenance_repo.get_all(start_date, end_date)
        
        return success_response({'maintenance_records': records, 'count': len(records)})
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/maintenance/<int:maintenance_id>', methods=['PUT'])
def update_maintenance_record(maintenance_id: int):
    """
    Update a maintenance record
    
    PUT /api/maintenance/<id>
    
    Request body:
        {
            "completion_date": "2024-12-16",
            "technician_notes": "Completed routine check. All systems normal.",
            "status": "completed"
        }
    
    Returns:
        200: Maintenance record updated successfully
        400: Validation error
        404: Maintenance record not found
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        # Check if maintenance record exists
        existing = maintenance_repo.get_by_id(maintenance_id)
        if not existing:
            return error_response(f"Maintenance record with ID {maintenance_id} not found", 404)
        
        # Update maintenance record
        success = maintenance_repo.update(maintenance_id, data)
        
        if success:
            updated_record = maintenance_repo.get_by_id(maintenance_id)
            return success_response(updated_record)
        else:
            return error_response("Failed to update maintenance record", 400)
            
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/equipment/<equipment_id>/maintenance', methods=['GET'])
def get_equipment_maintenance(equipment_id: str):
    """
    Get maintenance history for equipment
    
    GET /api/equipment/<id>/maintenance
    
    Returns:
        200: List of maintenance records for equipment
        404: Equipment not found
        500: Server error
    """
    try:
        # Check if equipment exists
        try:
            equipment_manager.get_equipment_status(equipment_id)
        except ValueError:
            return error_response(f"Equipment with ID '{equipment_id}' not found", 404)
        
        records = maintenance_repo.get_by_equipment(equipment_id)
        
        return success_response({
            'equipment_id': equipment_id,
            'maintenance_records': records,
            'count': len(records)
        })
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """
    User login
    
    POST /api/auth/login
    
    Request body:
        {
            "username": "operator1",
            "password": "password123"
        }
    
    Returns:
        200: Login successful with authentication token
        400: Missing credentials
        401: Invalid credentials
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return error_response("Username and password are required", 400)
        
        # Attempt login
        token = auth_service.login(username, password)
        
        if token:
            return success_response({
                'message': 'Login successful',
                'token': token,
                'username': username
            })
        else:
            return error_response("Invalid username or password", 401)
            
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """
    User registration
    
    POST /api/auth/register
    
    Request body:
        {
            "username": "newuser",
            "password": "password123",
            "role": "operator"
        }
    
    Returns:
        201: User registered successfully
        400: Validation error or username already exists
        500: Server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response("Request body is required", 400)
        
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'operator')
        
        if not username or not password:
            return error_response("Username and password are required", 400)
        
        # Create user
        result = auth_service.create_user(username, password, role)
        
        if result.success:
            return success_response(result.data, 201)
        else:
            return error_response(result.error_message, 400)
            
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)
