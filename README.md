# Industrial Equipment Monitoring System

A Python-based web application for monitoring industrial equipment, tracking sensor data, managing maintenance schedules, and providing alerting capabilities. This system is designed for workshop training purposes and demonstrates modern application development practices while intentionally including security vulnerabilities and performance issues for educational discovery and remediation.

## Overview

The Industrial Monitoring System (IMS) provides:

- **Equipment Registration**: Track industrial equipment (pumps, motors, conveyors, sensors)
- **Sensor Data Collection**: Record and query timestamped measurements (temperature, pressure, vibration)
- **Alert Management**: Automatic alerts when sensor readings exceed thresholds
- **Maintenance Tracking**: Schedule and track maintenance activities
- **Web Dashboard**: Interactive interface for monitoring system status
- **REST API**: JSON-based API for integration with external systems

## Workshop Learning Objectives

This application is designed to help participants learn:

1. **AI-Assisted Security Remediation**
   - Identify SQL injection vulnerabilities
   - Discover hardcoded credentials and secrets
   - Find missing authentication checks
   - Fix insecure password storage

2. **AI-Assisted Performance Optimization**
   - Identify N+1 query problems
   - Discover missing database indexes
   - Optimize inefficient algorithms
   - Reduce API payload sizes

3. **Property-Based Testing**
   - Write universal correctness properties
   - Use Hypothesis for automated test generation
   - Validate system behavior across input ranges

4. **Modern Deployment Practices**
   - Containerize applications with Docker
   - Configure multi-container setups
   - Manage environment-based configuration

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd industrial-monitoring-system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python app.py --init-db
   ```

5. **Generate sample data (optional)**
   ```bash
   python app.py --sample-data
   ```

## Usage

### Running Locally

Start the application server:

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Web Interface

Access the web dashboard at `http://localhost:5000`

**Available Pages:**
- `/` - Dashboard showing equipment and active alerts
- `/equipment/new` - Register new equipment
- `/equipment/<id>` - View equipment details
- `/sensors/record` - Record sensor readings
- `/maintenance` - View maintenance records
- `/alerts` - View and acknowledge alerts
- `/login` - User authentication

### REST API

The system provides a comprehensive REST API for programmatic access.

#### Equipment Endpoints

**Register Equipment**
```bash
POST /api/equipment
Content-Type: application/json

{
  "equipment_id": "PUMP-001",
  "name": "Main Water Pump",
  "type": "pump",
  "location": "Building A"
}
```

**List All Equipment**
```bash
GET /api/equipment
```

**Get Equipment Details**
```bash
GET /api/equipment/<equipment_id>
```

**Update Equipment**
```bash
PUT /api/equipment/<equipment_id>
Content-Type: application/json

{
  "name": "Updated Name",
  "location": "Building B"
}
```

**Delete Equipment**
```bash
DELETE /api/equipment/<equipment_id>
```

#### Sensor Endpoints

**Record Sensor Reading**
```bash
POST /api/sensors/readings
Content-Type: application/json

{
  "equipment_id": "PUMP-001",
  "sensor_type": "temperature",
  "value": 75.5,
  "unit": "celsius"
}
```

**Query Sensor Readings**
```bash
GET /api/sensors/readings?equipment_id=PUMP-001&start_date=2024-01-01&end_date=2024-12-31
```

**Get Equipment Sensor History**
```bash
GET /api/equipment/<equipment_id>/sensors
```

#### Alert Endpoints

**Get Active Alerts**
```bash
GET /api/alerts
```

**Acknowledge Alert**
```bash
POST /api/alerts/<alert_id>/ack
Content-Type: application/json

{
  "acknowledged_by": "operator1"
}
```

**Get Equipment Alerts**
```bash
GET /api/equipment/<equipment_id>/alerts
```

#### Maintenance Endpoints

**Create Maintenance Record**
```bash
POST /api/maintenance
Content-Type: application/json

{
  "equipment_id": "PUMP-001",
  "maintenance_type": "preventive",
  "scheduled_date": "2024-12-15",
  "description": "Quarterly inspection"
}
```

**List Maintenance Records**
```bash
GET /api/maintenance?equipment_id=PUMP-001
```

**Update Maintenance Record**
```bash
PUT /api/maintenance/<maintenance_id>
Content-Type: application/json

{
  "completion_date": "2024-12-15",
  "technician_notes": "Replaced worn bearings",
  "status": "completed"
}
```

**Get Equipment Maintenance History**
```bash
GET /api/equipment/<equipment_id>/maintenance
```

#### Authentication Endpoints

**User Login**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "operator1",
  "password": "password123"
}
```

**User Registration**
```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "password": "securepassword",
  "role": "operator"
}
```

### Configuration

The application uses `config.json` for configuration. Default settings:

```json
{
  "database": {
    "path": "industrial_monitoring.db"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": true
  },
  "thresholds": {
    "temperature": 80.0,
    "pressure": 100.0,
    "vibration": 5.0
  }
}
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Property-Based Tests Only

```bash
pytest -k "properties"
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
```

### View Coverage Report

```bash
open htmlcov/index.html  # On macOS
# or
xdg-open htmlcov/index.html  # On Linux
```

## Project Structure

```
industrial-monitoring-system/
├── app.py                      # Main application entry point
├── config.py                   # Configuration management
├── database.py                 # Database connection manager
├── schema.sql                  # Database schema
├── config.json                 # Configuration file
├── requirements.txt            # Python dependencies
├── repositories/               # Data access layer
│   ├── equipment.py
│   ├── sensor_data.py
│   ├── alerts.py
│   ├── maintenance.py
│   └── users.py
├── services/                   # Business logic layer
│   ├── equipment_manager.py
│   ├── sensor_processor.py
│   ├── alert_generator.py
│   └── auth_service.py
├── routes/                     # API and web routes
│   ├── api.py
│   └── web.py
├── templates/                  # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── equipment_form.html
│   └── ...
├── utils/                      # Utility modules
│   └── sample_data.py
└── test_*.py                   # Test files
```

## Workshop Activities

### Phase 1: Initial Setup (15 minutes)
1. Clone and set up the application
2. Review the requirements document
3. Run the application locally
4. Explore the web interface and API

### Phase 2: Code Review (30 minutes)
1. Use AI tools to analyze the codebase
2. Review `SECURITY_ISSUES.md` for hints
3. Review `PERFORMANCE_ISSUES.md` for hints
4. Document your findings

### Phase 3: Security Remediation (45 minutes)
1. Fix SQL injection vulnerabilities
2. Remove hardcoded secrets
3. Implement secure password hashing
4. Add authentication to unprotected endpoints
5. Verify fixes with property-based tests

### Phase 4: Performance Optimization (45 minutes)
1. Fix N+1 query problems
2. Add database indexes
3. Optimize inefficient algorithms
4. Implement API pagination
5. Verify improvements with tests

### Phase 5: Containerization (30 minutes)
1. Create Dockerfile
2. Build and test container
3. Create Docker Compose configuration
4. Deploy multi-container setup

## Dependencies

- **Flask 3.0.0**: Web framework
- **Hypothesis 6.92.0**: Property-based testing
- **pytest 7.4.3**: Testing framework
- **PyYAML 6.0.1**: YAML configuration support

## License

This project is for educational purposes only.

## Support

For questions or issues during the workshop, please consult:
- `SECURITY_ISSUES.md` for security vulnerability hints
- `PERFORMANCE_ISSUES.md` for performance optimization hints
- Workshop facilitators for guidance

## Contributing

This is a training application with intentional flaws. Contributions should maintain the educational nature of the codebase.
