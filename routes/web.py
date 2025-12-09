"""
Web UI Routes for Industrial Monitoring System
Provides HTML interface for local testing and interaction
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date
from typing import Optional
from services.equipment_manager import EquipmentManager
from services.sensor_processor import SensorProcessor
from services.alert_generator import AlertGenerator
from services.auth_service import AuthService
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository
from repositories.alerts import AlertRepository
from repositories.maintenance import MaintenanceRepository
from repositories.users import UserRepository
from database import DatabaseManager


# Create Blueprint for web UI routes
web_bp = Blueprint('web', __name__)

# Global service instances (will be initialized by app)
equipment_manager: Optional[EquipmentManager] = None
sensor_processor: Optional[SensorProcessor] = None
alert_generator: Optional[AlertGenerator] = None
auth_service: Optional[AuthService] = None
maintenance_repo: Optional[MaintenanceRepository] = None
sensor_repo: Optional[SensorDataRepository] = None


def init_web_services(db_manager: DatabaseManager):
    """
    Initialize web UI service instances
    
    Args:
        db_manager: DatabaseManager instance
    """
    global equipment_manager, sensor_processor, alert_generator, auth_service, maintenance_repo, sensor_repo
    
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


# ============================================================================
# Dashboard Route
# ============================================================================

@web_bp.route('/')
def dashboard():
    """
    Display dashboard with equipment list and active alerts
    
    GET /
    
    Shows:
    - All registered equipment with latest sensor readings
    - Active alerts
    """
    try:
        # Get all equipment
        equipment_list = equipment_manager.list_all_equipment()
        
        # Get latest sensor reading for each equipment
        for equipment in equipment_list:
            readings = sensor_repo.get_by_equipment(equipment['equipment_id'], limit=1)
            equipment['latest_reading'] = readings[0] if readings else None
        
        # Get active alerts
        alerts = alert_generator.get_active_alerts()
        
        return render_template(
            'dashboard.html',
            equipment=equipment_list,
            alerts=alerts
        )
    except Exception as e:
        return render_template(
            'dashboard.html',
            equipment=[],
            alerts=[],
            error=f"Error loading dashboard: {str(e)}"
        )


# ============================================================================
# Equipment Routes
# ============================================================================

@web_bp.route('/equipment/new', methods=['GET', 'POST'])
def equipment_new():
    """
    Equipment registration form
    
    GET /equipment/new - Display registration form
    POST /equipment/new - Handle equipment registration
    """
    if request.method == 'POST':
        try:
            # Get form data
            equipment_data = {
                'equipment_id': request.form.get('equipment_id'),
                'name': request.form.get('name'),
                'type': request.form.get('type'),
                'location': request.form.get('location'),
                'status': request.form.get('status', 'active')
            }
            
            # Register equipment
            result = equipment_manager.register_equipment(equipment_data)
            
            if result.success:
                return render_template(
                    'equipment_form.html',
                    success=True
                )
            else:
                return render_template(
                    'equipment_form.html',
                    error=result.error_message
                )
        except Exception as e:
            return render_template(
                'equipment_form.html',
                error=f"Error registering equipment: {str(e)}"
            )
    
    # GET request - show form
    return render_template('equipment_form.html')


@web_bp.route('/equipment/<equipment_id>')
def equipment_detail(equipment_id: str):
    """
    Equipment detail page
    
    GET /equipment/<id>
    
    Shows:
    - Equipment details
    - Recent sensor readings
    - Alerts for this equipment
    - Maintenance history
    """
    try:
        # Get equipment details
        equipment = equipment_manager.get_equipment_status(equipment_id)
        
        # Get recent sensor readings (last 20)
        sensor_readings = sensor_repo.get_by_equipment(equipment_id, limit=20)
        
        # Get alerts for this equipment
        alerts = alert_generator.get_equipment_alerts(equipment_id)
        
        # Get maintenance records for this equipment
        maintenance_records = maintenance_repo.get_by_equipment(equipment_id)
        
        return render_template(
            'equipment_detail.html',
            equipment=equipment,
            sensor_readings=sensor_readings,
            alerts=alerts,
            maintenance_records=maintenance_records
        )
    except ValueError as e:
        return render_template(
            'dashboard.html',
            equipment=[],
            alerts=[],
            error=str(e)
        )
    except Exception as e:
        return render_template(
            'dashboard.html',
            equipment=[],
            alerts=[],
            error=f"Error loading equipment details: {str(e)}"
        )


@web_bp.route('/equipment/<equipment_id>/edit', methods=['GET', 'POST'])
def equipment_edit(equipment_id: str):
    """
    Equipment edit form
    
    GET /equipment/<id>/edit - Display edit form
    POST /equipment/<id>/edit - Handle equipment update
    """
    if request.method == 'POST':
        try:
            # Get form data
            equipment_data = {
                'name': request.form.get('name'),
                'type': request.form.get('type'),
                'location': request.form.get('location'),
                'status': request.form.get('status', 'active')
            }
            
            # Update equipment
            result = equipment_manager.update_equipment(equipment_id, equipment_data)
            
            if result.success:
                return redirect(url_for('web.equipment_detail', equipment_id=equipment_id))
            else:
                equipment = equipment_manager.get_equipment_status(equipment_id)
                return render_template(
                    'equipment_edit.html',
                    equipment=equipment,
                    error=result.error_message
                )
        except Exception as e:
            equipment = equipment_manager.get_equipment_status(equipment_id)
            return render_template(
                'equipment_edit.html',
                equipment=equipment,
                error=f"Error updating equipment: {str(e)}"
            )
    
    # GET request - show edit form
    try:
        equipment = equipment_manager.get_equipment_status(equipment_id)
        return render_template('equipment_edit.html', equipment=equipment)
    except ValueError as e:
        return redirect(url_for('web.dashboard'))


@web_bp.route('/equipment/<equipment_id>/delete', methods=['POST'])
def equipment_delete(equipment_id: str):
    """
    Delete equipment
    
    POST /equipment/<id>/delete
    """
    try:
        result = equipment_manager.delete_equipment(equipment_id)
        
        if result.success:
            return redirect(url_for('web.dashboard'))
        else:
            return redirect(url_for('web.equipment_detail', equipment_id=equipment_id))
    except Exception as e:
        return redirect(url_for('web.equipment_detail', equipment_id=equipment_id))


# ============================================================================
# Sensor Routes
# ============================================================================

@web_bp.route('/sensors/record', methods=['GET', 'POST'])
def sensor_record():
    """
    Sensor reading form
    
    GET /sensors/record - Display sensor reading form
    POST /sensors/record - Handle sensor reading submission
    """
    # Get equipment list for dropdown
    equipment_list = equipment_manager.list_all_equipment()
    
    if request.method == 'POST':
        try:
            # Get form data
            reading_data = {
                'equipment_id': request.form.get('equipment_id'),
                'sensor_type': request.form.get('sensor_type'),
                'value': float(request.form.get('value')),
                'unit': request.form.get('unit', '')
            }
            
            # Record sensor reading
            result = sensor_processor.record_reading(reading_data)
            
            if result.success:
                # Check if alert was generated
                alert_generated = 'alert' in result.data
                alert_message = result.data.get('alert', {}).get('message', '') if alert_generated else ''
                
                # If alert was generated, create it in the database
                if alert_generated:
                    alert_data = result.data['alert']
                    alert_generator.generate_alert(
                        alert_data['equipment_id'],
                        alert_data['alert_type'],
                        alert_data['severity'],
                        alert_data['message']
                    )
                
                return render_template(
                    'sensor_form.html',
                    equipment=equipment_list,
                    success=True,
                    alert_generated=alert_generated,
                    alert_message=alert_message
                )
            else:
                return render_template(
                    'sensor_form.html',
                    equipment=equipment_list,
                    error=result.error_message
                )
        except ValueError as e:
            return render_template(
                'sensor_form.html',
                equipment=equipment_list,
                error=f"Invalid value: {str(e)}"
            )
        except Exception as e:
            return render_template(
                'sensor_form.html',
                equipment=equipment_list,
                error=f"Error recording sensor reading: {str(e)}"
            )
    
    # GET request - show form
    return render_template('sensor_form.html', equipment=equipment_list)


# ============================================================================
# Maintenance Routes
# ============================================================================

@web_bp.route('/maintenance')
def maintenance_list():
    """
    Maintenance records list
    
    GET /maintenance
    
    Query parameters:
    - equipment_id: Filter by equipment ID
    - status: Filter by status
    
    Shows:
    - Overdue maintenance records
    - All maintenance records with optional filters
    """
    try:
        # Get query parameters
        equipment_id = request.args.get('equipment_id')
        status = request.args.get('status')
        
        # Get maintenance records
        if equipment_id:
            maintenance_records = maintenance_repo.get_by_equipment(equipment_id)
        elif status:
            maintenance_records = maintenance_repo.get_by_status(status)
        else:
            maintenance_records = maintenance_repo.get_all()
        
        # Get overdue maintenance
        overdue_maintenance = maintenance_repo.get_overdue()
        
        # Calculate days overdue for each overdue record
        today = date.today()
        for record in overdue_maintenance:
            scheduled = datetime.fromisoformat(record['scheduled_date']).date()
            days_overdue = (today - scheduled).days
            record['days_overdue'] = days_overdue
        
        return render_template(
            'maintenance_list.html',
            maintenance_records=maintenance_records,
            overdue_maintenance=overdue_maintenance
        )
    except Exception as e:
        return render_template(
            'maintenance_list.html',
            maintenance_records=[],
            overdue_maintenance=[],
            error=f"Error loading maintenance records: {str(e)}"
        )


# ============================================================================
# Alert Routes
# ============================================================================

@web_bp.route('/alerts')
def alert_list():
    """
    Alert list page
    
    GET /alerts
    
    Shows:
    - Active alerts
    - Acknowledged alerts
    - Alert statistics
    """
    try:
        # Get all alerts
        all_alerts = alert_generator.get_all_alerts()
        
        # Separate active and acknowledged alerts
        active_alerts = [a for a in all_alerts if a['status'] == 'active']
        acknowledged_alerts = [a for a in all_alerts if a['status'] == 'acknowledged']
        
        # Calculate severity counts
        severity_counts = {
            'critical': len([a for a in all_alerts if a['severity'] == 'critical']),
            'high': len([a for a in all_alerts if a['severity'] == 'high']),
            'medium': len([a for a in all_alerts if a['severity'] == 'medium']),
            'low': len([a for a in all_alerts if a['severity'] == 'low'])
        }
        
        return render_template(
            'alert_list.html',
            active_alerts=active_alerts,
            acknowledged_alerts=acknowledged_alerts,
            severity_counts=severity_counts
        )
    except Exception as e:
        return render_template(
            'alert_list.html',
            active_alerts=[],
            acknowledged_alerts=[],
            severity_counts={},
            error=f"Error loading alerts: {str(e)}"
        )


@web_bp.route('/alerts/<int:alert_id>/ack', methods=['POST'])
def alert_acknowledge(alert_id: int):
    """
    Acknowledge an alert
    
    POST /alerts/<id>/ack
    
    Acknowledges the alert and redirects back to the referring page
    """
    try:
        # Get user from session or use default
        user = session.get('username', 'operator')
        
        # Acknowledge alert
        result = alert_generator.acknowledge_alert(alert_id, user)
        
        if result.success:
            # Redirect to referrer or alerts page
            referrer = request.referrer
            if referrer and ('dashboard' in referrer or 'equipment' in referrer):
                return redirect(referrer)
            else:
                return redirect(url_for('web.alert_list', success='Alert acknowledged successfully'))
        else:
            return redirect(url_for('web.alert_list', error=result.error_message))
    except Exception as e:
        return redirect(url_for('web.alert_list', error=f"Error acknowledging alert: {str(e)}"))


# ============================================================================
# Authentication Routes
# ============================================================================

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page
    
    GET /login - Display login form
    POST /login - Handle login submission
    """
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                return render_template(
                    'login.html',
                    error="Username and password are required"
                )
            
            # Attempt login
            token = auth_service.login(username, password)
            
            if token:
                # Store username in session
                session['username'] = username
                session['token'] = token
                
                return render_template(
                    'login.html',
                    success=f"Login successful! Welcome, {username}."
                )
            else:
                return render_template(
                    'login.html',
                    error="Invalid username or password"
                )
        except Exception as e:
            return render_template(
                'login.html',
                error=f"Error during login: {str(e)}"
            )
    
    # GET request - show login form
    return render_template('login.html')


@web_bp.route('/logout')
def logout():
    """
    Logout user
    
    GET /logout - Clear session and redirect to dashboard
    """
    session.clear()
    return redirect(url_for('web.dashboard'))
