"""
Database Manager for Industrial Monitoring System
Handles SQLite database connections and schema initialization
"""

import sqlite3
import os
from typing import List, Dict, Optional, Any, Tuple
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database connections and operations"""
    
    def __init__(self, db_path: str = "industrial_monitoring.db"):
        """
        Initialize DatabaseManager with database path
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection = None
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get or create a database connection
        
        Returns:
            sqlite3.Connection: Active database connection
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor operations
        
        Yields:
            sqlite3.Cursor: Database cursor for executing queries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries
        
        Args:
            query: SQL SELECT query
            params: Query parameters for parameterized queries
            
        Returns:
            List of dictionaries representing query results
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query
        
        Args:
            query: SQL INSERT/UPDATE/DELETE query
            params: Query parameters for parameterized queries
            
        Returns:
            Number of affected rows or last inserted row ID
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            # Return lastrowid for INSERT, rowcount for UPDATE/DELETE
            if query.strip().upper().startswith('INSERT'):
                return cursor.lastrowid
            return cursor.rowcount
    
    def init_schema(self, schema_file: str = "schema.sql"):
        """
        Initialize database schema from SQL file
        
        Args:
            schema_file: Path to SQL schema file
        """
        if not os.path.exists(schema_file):
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema creation
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.executescript(schema_sql)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
