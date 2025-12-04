"""
Sample Data Generator for Industrial Monitoring System
Generates random test data for equipment, sensors, alerts, and maintenance records
"""

import random
from datetime import datetime, timedelta, date
from typing import List, Dict
from database import DatabaseManager
from repositories.equipment import EquipmentRepository
from repositories.sensor_data import SensorDataRepository
from repositories.alerts import AlertRepository
from repositories.maintenance import MaintenanceRepository


class SampleDataGenerator:
    """Utility class for generating sample data for testing and demonstration"""
    
    # Equipment types and their typical sensor types
    EQUIPMENT_TYPES = {
        'pumpe': ['pressure', 'temperature', 'vibration', 'flow_rate'],
        'motor': ['temperature', 'vibration', 'current', 'rpm'],
        'förderband': ['speed', 'temperature', 'vibration', 'load'],
        'sensor': ['temperature', 'humidity', 'pressure'],
        'kompressor': ['pressure', 'temperature', 'vibration', 'power'],
        'ventil': ['position', 'pressure', 'temperature'],
        'tank': ['level', 'temperature', 'pressure']
    }
    
    EQUIPMENT_NAMES = {
        'pumpe': ['Hauptwasserpumpe', 'Kühlmittelpumpe', 'Hydraulikpumpe', 'Druckpumpe', 'Umwälzpumpe'],
        'motor': ['Antriebsmotor', 'Hauptmotor', 'Hilfsmotor', 'Fördermotor', 'Lüftermotor'],
        'förderband': ['Transportband', 'Förderanlage', 'Hauptförderband', 'Sortierband', 'Verpackungsband'],
        'sensor': ['Temperatursensor', 'Drucksensor', 'Feuchtigkeitssensor', 'Positionssensor', 'Füllstandssensor'],
        'kompressor': ['Druckluftkompressor', 'Hauptkompressor', 'Hilfskompressor', 'Kühlkompressor', 'Vakuumkompressor'],
        'ventil': ['Regelventil', 'Absperrventil', 'Sicherheitsventil', 'Druckventil', 'Steuerventil'],
        'tank': ['Lagertank', 'Drucktank', 'Vorratstank', 'Puffertank', 'Sammeltank']
    }
    
    LOCATIONS = [
        'Gebäude A - Etage 1',
        'Gebäude A - Etage 2',
        'Gebäude B - Etage 1',
        'Gebäude B - Etage 2',
        'Lager - Bereich 1',
        'Lager - Bereich 2',
        'Produktionslinie 1',
        'Produktionslinie 2',
        'Technikraum',
        'Wartungshalle'
    ]
    
    ALERT_TYPES = [
        'schwellwert_überschritten',
        'geräteausfall',
        'wartung_erforderlich',
        'sensor_fehlfunktion',
        'abnormale_messung'
    ]
    
    ALERT_TYPE_NAMES = {
        'schwellwert_überschritten': 'Schwellwert überschritten',
        'geräteausfall': 'Geräteausfall',
        'wartung_erforderlich': 'Wartung erforderlich',
        'sensor_fehlfunktion': 'Sensor-Fehlfunktion',
        'abnormale_messung': 'Abnormale Messung'
    }
    
    SEVERITIES = ['niedrig', 'mittel', 'hoch', 'kritisch']
    
    MAINTENANCE_TYPES = [
        'vorbeugend',
        'korrigierend',
        'inspektion',
        'kalibrierung',
        'reinigung',
        'reparatur'
    ]
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize SampleDataGenerator
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager
        self.equipment_repo = EquipmentRepository(db_manager)
        self.sensor_repo = SensorDataRepository(db_manager)
        self.alert_repo = AlertRepository(db_manager)
        self.maintenance_repo = MaintenanceRepository(db_manager)
    
    def generate_equipment(self, count: int = 10) -> List[Dict]:
        """
        Generate random equipment records
        
        Args:
            count: Number of equipment records to generate
            
        Returns:
            List of equipment dictionaries
        """
        equipment_list = []
        
        for i in range(count):
            equipment_type = random.choice(list(self.EQUIPMENT_TYPES.keys()))
            # Get a random German name for this equipment type
            german_names = self.EQUIPMENT_NAMES.get(equipment_type, [equipment_type.title()])
            name = random.choice(german_names)
            
            equipment = {
                'equipment_id': f"{equipment_type.upper()}-{i+1:03d}",
                'name': f"{name} {i+1}",
                'type': equipment_type,
                'location': random.choice(self.LOCATIONS),
                'status': random.choice(['active', 'active', 'active', 'maintenance', 'inactive'])
            }
            equipment_list.append(equipment)
        
        return equipment_list
    
    def generate_sensor_readings(self, equipment_id: str, equipment_type: str, 
                                count: int = 50) -> List[Dict]:
        """
        Generate random sensor readings for a specific equipment
        
        Args:
            equipment_id: Equipment identifier
            equipment_type: Type of equipment (determines sensor types)
            count: Number of sensor readings to generate
            
        Returns:
            List of sensor reading dictionaries
        """
        readings = []
        sensor_types = self.EQUIPMENT_TYPES.get(equipment_type, ['temperature', 'pressure'])
        
        # Generate readings over the past 7 days
        now = datetime.now()
        
        for i in range(count):
            # Distribute readings over the past week
            time_offset = timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            timestamp = now - time_offset
            
            sensor_type = random.choice(sensor_types)
            
            # Generate realistic values based on sensor type
            value, unit = self._generate_sensor_value(sensor_type)
            
            reading = {
                'equipment_id': equipment_id,
                'sensor_type': sensor_type,
                'value': value,
                'unit': unit,
                'timestamp': timestamp.isoformat()
            }
            readings.append(reading)
        
        return readings
    
    def _generate_sensor_value(self, sensor_type: str) -> tuple:
        """
        Generate realistic sensor value and unit based on sensor type
        
        Args:
            sensor_type: Type of sensor
            
        Returns:
            Tuple of (value, unit)
        """
        sensor_ranges = {
            'temperature': (20.0, 100.0, '°C'),
            'pressure': (0.5, 10.0, 'bar'),
            'vibration': (0.0, 5.0, 'mm/s'),
            'flow_rate': (10.0, 500.0, 'L/min'),
            'current': (5.0, 50.0, 'A'),
            'rpm': (500.0, 3000.0, 'rpm'),
            'speed': (0.5, 5.0, 'm/s'),
            'load': (0.0, 100.0, '%'),
            'humidity': (30.0, 80.0, '%'),
            'power': (1.0, 100.0, 'kW'),
            'position': (0.0, 100.0, '%'),
            'level': (0.0, 100.0, '%')
        }
        
        if sensor_type in sensor_ranges:
            min_val, max_val, unit = sensor_ranges[sensor_type]
            value = round(random.uniform(min_val, max_val), 2)
        else:
            value = round(random.uniform(0.0, 100.0), 2)
            unit = 'units'
        
        return value, unit
    
    def generate_alerts(self, equipment_ids: List[str], count: int = 20) -> List[Dict]:
        """
        Generate random alert records
        
        Args:
            equipment_ids: List of equipment IDs to generate alerts for
            count: Number of alerts to generate
            
        Returns:
            List of alert dictionaries
        """
        if not equipment_ids:
            return []
        
        alerts = []
        
        for i in range(count):
            equipment_id = random.choice(equipment_ids)
            alert_type = random.choice(self.ALERT_TYPES)
            severity = random.choice(self.SEVERITIES)
            
            # Generate appropriate German message based on alert type
            messages = {
                'schwellwert_überschritten': f"Sensorwert hat Schwellwert überschritten für {equipment_id}",
                'geräteausfall': f"Gerät {equipment_id} ist ausgefallen und erfordert sofortige Aufmerksamkeit",
                'wartung_erforderlich': f"Geplante Wartung fällig für {equipment_id}",
                'sensor_fehlfunktion': f"Sensor-Fehlfunktion erkannt bei {equipment_id}",
                'abnormale_messung': f"Abnormale Sensormessung erkannt bei {equipment_id}"
            }
            
            message = messages.get(alert_type, f"Alarm für {equipment_id}")
            
            # Some alerts should be acknowledged
            status = random.choice(['active', 'active', 'active', 'acknowledged'])
            
            alert = {
                'equipment_id': equipment_id,
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                'status': status
            }
            alerts.append(alert)
        
        return alerts
    
    def generate_maintenance_records(self, equipment_ids: List[str], 
                                    count: int = 30) -> List[Dict]:
        """
        Generate random maintenance records
        
        Args:
            equipment_ids: List of equipment IDs to generate maintenance records for
            count: Number of maintenance records to generate
            
        Returns:
            List of maintenance record dictionaries
        """
        if not equipment_ids:
            return []
        
        records = []
        today = date.today()
        
        for i in range(count):
            equipment_id = random.choice(equipment_ids)
            maintenance_type = random.choice(self.MAINTENANCE_TYPES)
            
            # Generate scheduled dates: some past (overdue), some future
            days_offset = random.randint(-30, 60)
            scheduled_date = (today + timedelta(days=days_offset)).isoformat()
            
            # Determine status based on scheduled date
            if days_offset < -7:
                # Past maintenance - likely completed or overdue
                status = random.choice(['completed', 'completed', 'scheduled'])
            elif days_offset < 0:
                # Recently past - might be overdue
                status = random.choice(['completed', 'scheduled', 'in_progress'])
            else:
                # Future maintenance
                status = 'scheduled'
            
            # German maintenance descriptions
            maintenance_descriptions = {
                'vorbeugend': f"Vorbeugende Wartung für {equipment_id}",
                'korrigierend': f"Korrigierende Wartung für {equipment_id}",
                'inspektion': f"Inspektion von {equipment_id}",
                'kalibrierung': f"Kalibrierung von {equipment_id}",
                'reinigung': f"Reinigung von {equipment_id}",
                'reparatur': f"Reparatur von {equipment_id}"
            }
            
            description = maintenance_descriptions.get(maintenance_type, f"Wartung für {equipment_id}")
            
            record = {
                'equipment_id': equipment_id,
                'maintenance_type': maintenance_type,
                'scheduled_date': scheduled_date,
                'description': description,
                'status': status
            }
            
            # Add completion details for completed maintenance
            if status == 'completed':
                completion_offset = random.randint(0, 3)
                completion_date = (datetime.fromisoformat(scheduled_date).date() + 
                                 timedelta(days=completion_offset)).isoformat()
                record['completion_date'] = completion_date
                
                # German technician notes
                completion_notes = {
                    'vorbeugend': "Vorbeugende Wartung erfolgreich abgeschlossen",
                    'korrigierend': "Korrigierende Maßnahmen erfolgreich durchgeführt",
                    'inspektion': "Inspektion abgeschlossen, keine Mängel festgestellt",
                    'kalibrierung': "Kalibrierung erfolgreich durchgeführt",
                    'reinigung': "Reinigung abgeschlossen",
                    'reparatur': "Reparatur erfolgreich abgeschlossen"
                }
                record['technician_notes'] = completion_notes.get(maintenance_type, "Wartung abgeschlossen")
            
            records.append(record)
        
        return records
    
    def populate_database(self, equipment_count: int = 10,
                         readings_per_equipment: int = 50,
                         alert_count: int = 20,
                         maintenance_count: int = 30):
        """
        Populate database with sample data
        
        Args:
            equipment_count: Number of equipment records to create
            readings_per_equipment: Number of sensor readings per equipment
            alert_count: Number of alerts to create
            maintenance_count: Number of maintenance records to create
        """
        print(f"Generating {equipment_count} equipment records...")
        equipment_list = self.generate_equipment(equipment_count)
        equipment_ids = []
        
        # Create equipment records
        for equipment in equipment_list:
            try:
                self.equipment_repo.create(equipment)
                equipment_ids.append(equipment['equipment_id'])
                print(f"  Created equipment: {equipment['equipment_id']}")
            except Exception as e:
                print(f"  Error creating equipment {equipment['equipment_id']}: {e}")
        
        # Generate sensor readings for each equipment
        print(f"\nGenerating sensor readings ({readings_per_equipment} per equipment)...")
        total_readings = 0
        for equipment in equipment_list:
            readings = self.generate_sensor_readings(
                equipment['equipment_id'],
                equipment['type'],
                readings_per_equipment
            )
            for reading in readings:
                try:
                    self.sensor_repo.create(reading)
                    total_readings += 1
                except Exception as e:
                    print(f"  Error creating sensor reading: {e}")
        print(f"  Created {total_readings} sensor readings")
        
        # Generate alerts
        print(f"\nGenerating {alert_count} alerts...")
        alerts = self.generate_alerts(equipment_ids, alert_count)
        created_alerts = 0
        for alert in alerts:
            try:
                self.alert_repo.create(alert)
                created_alerts += 1
            except Exception as e:
                print(f"  Error creating alert: {e}")
        print(f"  Created {created_alerts} alerts")
        
        # Generate maintenance records
        print(f"\nGenerating {maintenance_count} maintenance records...")
        maintenance_records = self.generate_maintenance_records(equipment_ids, maintenance_count)
        created_maintenance = 0
        for record in maintenance_records:
            try:
                # Handle completion_date separately for update
                completion_date = record.pop('completion_date', None)
                technician_notes = record.pop('technician_notes', None)
                
                record_id = self.maintenance_repo.create(record)
                
                # Update with completion details if present
                if completion_date and technician_notes:
                    self.maintenance_repo.update(record_id, {
                        'completion_date': completion_date,
                        'technician_notes': technician_notes
                    })
                
                created_maintenance += 1
            except Exception as e:
                print(f"  Error creating maintenance record: {e}")
        print(f"  Created {created_maintenance} maintenance records")
        
        print("\nSample data generation complete!")
        print(f"Summary:")
        print(f"  - Equipment: {len(equipment_ids)}")
        print(f"  - Sensor Readings: {total_readings}")
        print(f"  - Alerts: {created_alerts}")
        print(f"  - Maintenance Records: {created_maintenance}")
