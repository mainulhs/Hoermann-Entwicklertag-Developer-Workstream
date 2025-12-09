-- Industrial Monitoring System Database Schema
-- This schema intentionally omits indexes on sensor_readings for workshop learning purposes

-- Equipment table: stores registered industrial equipment
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    location TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sensor readings table: stores time-series sensor data
-- INTENTIONAL FLAW: Missing indexes on equipment_id and timestamp for performance issues
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
);

-- Alerts table: stores equipment alerts and notifications
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
);

-- Maintenance table: stores maintenance schedules and records
CREATE TABLE IF NOT EXISTS maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT NOT NULL,
    maintenance_type TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    completion_date DATE,
    description TEXT,
    technician_notes TEXT,
    status TEXT DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
);

-- Users table: stores user authentication data
-- INTENTIONAL FLAW: Passwords stored in plain text for security workshop
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'operator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
-- These indexes significantly improve query performance for common operations

-- Index for sensor readings by equipment (used in dashboard and equipment detail pages)
CREATE INDEX IF NOT EXISTS idx_sensor_readings_equipment ON sensor_readings(equipment_id);

-- Index for sensor readings by timestamp (used for time-based queries)
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC);

-- Composite index for equipment + timestamp (optimizes latest reading queries)
CREATE INDEX IF NOT EXISTS idx_sensor_readings_equipment_timestamp ON sensor_readings(equipment_id, timestamp DESC);

-- Index for alerts by equipment
CREATE INDEX IF NOT EXISTS idx_alerts_equipment ON alerts(equipment_id);

-- Index for alerts by status (used for active alerts queries)
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);

-- Index for maintenance by equipment
CREATE INDEX IF NOT EXISTS idx_maintenance_equipment ON maintenance(equipment_id);

-- Index for maintenance by scheduled date (used for overdue maintenance)
CREATE INDEX IF NOT EXISTS idx_maintenance_scheduled_date ON maintenance(scheduled_date);
