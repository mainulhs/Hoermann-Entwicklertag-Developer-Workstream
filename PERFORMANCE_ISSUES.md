# Performance Issues Guide

This document describes the intentional performance problems included in the Industrial Monitoring System for educational purposes. Each issue includes hints for discovery and guidance for optimization using AI-assisted development tools.

⚠️ **NOTE**: These performance issues are intentional for learning purposes and demonstrate common real-world problems.

## Overview

The application contains four major categories of performance issues:

1. N+1 Query Problem
2. Missing Database Indexes
3. Inefficient Algorithm Implementation
4. Large API Payloads Without Pagination

## Performance Issue 1: N+1 Query Problem

### Description

The dashboard retrieves the latest sensor reading for each piece of equipment by executing a separate database query for each equipment item, resulting in N+1 queries (1 query for equipment list + N queries for sensor readings).

### Location

**File**: `repositories/sensor_data.py`  
**Method**: `SensorDataRepository.get_latest_readings()`

### Hints for Discovery

1. Monitor database queries when loading the dashboard
2. Add query logging to see how many queries execute
3. Use AI tools to analyze query patterns:
   - "Find N+1 query problems in this code"
   - "Analyze database access patterns for inefficiencies"
4. Profile the application with many equipment items
5. Look for loops that execute queries inside them

### Problematic Code Pattern

```python
class SensorDataRepository:
    def get_latest_readings(self) -> List[Dict]:
        # INEFFICIENT: N+1 query problem
        equipment_list = self.equipment_repo.get_all()  # 1 query
        results = []
        
        for equipment in equipment_list:  # N queries
            # Separate query for EACH equipment!
            reading = self.get_latest_for_equipment(equipment['equipment_id'])
            results.append({
                'equipment': equipment,
                'reading': reading
            })
        
        return results
```

### Performance Impact

**With 100 equipment items:**
- Current: 101 database queries (1 + 100)
- Query time: ~500ms - 1000ms
- Database load: High
- Scalability: Poor (linear growth with equipment count)

**Symptoms:**
- Slow dashboard loading
- High database CPU usage
- Increased latency under load
- Poor user experience

### Remediation Guidance

**AI Prompts to Use:**
- "Fix the N+1 query problem in this method"
- "Optimize this code to use a single database query"
- "Rewrite this using a JOIN to eliminate multiple queries"

**Optimized Implementation (Option 1: Single Query with JOIN):**

```python
class SensorDataRepository:
    def get_latest_readings(self) -> List[Dict]:
        # OPTIMIZED: Single query with JOIN and subquery
        sql = """
            SELECT 
                e.*,
                sr.sensor_type,
                sr.value,
                sr.unit,
                sr.timestamp
            FROM equipment e
            LEFT JOIN sensor_readings sr ON e.equipment_id = sr.equipment_id
            WHERE sr.id IN (
                SELECT id FROM sensor_readings sr2
                WHERE sr2.equipment_id = e.equipment_id
                ORDER BY sr2.timestamp DESC
                LIMIT 1
            )
            OR sr.id IS NULL
        """
        
        results = self.db.execute_query(sql, ())
        return self._format_results(results)
```

**Optimized Implementation (Option 2: Window Function):**

```python
class SensorDataRepository:
    def get_latest_readings(self) -> List[Dict]:
        # OPTIMIZED: Using window function (SQLite 3.25+)
        sql = """
            WITH ranked_readings AS (
                SELECT 
                    equipment_id,
                    sensor_type,
                    value,
                    unit,
                    timestamp,
                    ROW_NUMBER() OVER (
                        PARTITION BY equipment_id 
                        ORDER BY timestamp DESC
                    ) as rn
                FROM sensor_readings
            )
            SELECT 
                e.*,
                r.sensor_type,
                r.value,
                r.unit,
                r.timestamp
            FROM equipment e
            LEFT JOIN ranked_readings r 
                ON e.equipment_id = r.equipment_id AND r.rn = 1
        """
        
        results = self.db.execute_query(sql, ())
        return self._format_results(results)
```

**Key Principles:**
- Minimize database round trips
- Use JOINs to fetch related data in one query
- Leverage database features (window functions, subqueries)
- Batch operations when possible
- Use eager loading instead of lazy loading

### Validation

**Before Optimization:**

```python
import time
import sqlite3

# Enable query logging
sqlite3.enable_callback_tracebacks(True)

start = time.time()
readings = sensor_repo.get_latest_readings()
end = time.time()

print(f"Time: {end - start:.3f}s")
print(f"Queries executed: {query_counter}")
# Expected: ~101 queries, 500-1000ms
```

**After Optimization:**

```python
start = time.time()
readings = sensor_repo.get_latest_readings()
end = time.time()

print(f"Time: {end - start:.3f}s")
print(f"Queries executed: {query_counter}")
# Expected: 1 query, 50-100ms (5-10x faster!)
```

**Performance Comparison:**

| Equipment Count | Before (queries) | After (queries) | Speedup |
|----------------|------------------|-----------------|---------|
| 10             | 11               | 1               | 5x      |
| 100            | 101              | 1               | 10x     |
| 1000           | 1001             | 1               | 50x     |

---

## Performance Issue 2: Missing Database Indexes

### Description

The `sensor_readings` table lacks indexes on frequently queried columns (`equipment_id` and `timestamp`), causing full table scans and slow query performance.

### Location

**File**: `schema.sql`  
**Table**: `sensor_readings`

### Hints for Discovery

1. Use `EXPLAIN QUERY PLAN` to analyze query execution
2. Monitor query performance with large datasets
3. Use AI tools:
   - "Analyze this database schema for missing indexes"
   - "Find performance issues in these SQL queries"
4. Profile queries that filter by equipment_id or timestamp
5. Check for SCAN operations in query plans

### Problematic Schema

```sql
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
);
-- MISSING: No indexes on equipment_id or timestamp!
```

### Performance Impact

**Query Performance Without Indexes:**

```sql
-- Query: Get readings for specific equipment
SELECT * FROM sensor_readings 
WHERE equipment_id = 'PUMP-001' 
ORDER BY timestamp DESC 
LIMIT 10;

-- Execution: SCAN sensor_readings (full table scan)
-- Time: 500ms with 100,000 rows
```

**Symptoms:**
- Slow sensor data queries
- Dashboard lag when filtering by equipment
- Poor performance with time range queries
- High CPU usage during queries

### Remediation Guidance

**AI Prompts to Use:**
- "Add appropriate indexes to this database schema"
- "What indexes should I create for these queries?"
- "Optimize this table for queries filtering by equipment_id and timestamp"

**Optimized Schema:**

```sql
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id TEXT NOT NULL,
    sensor_type TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
);

-- OPTIMIZED: Add indexes for common query patterns
CREATE INDEX idx_sensor_readings_equipment 
    ON sensor_readings(equipment_id);

CREATE INDEX idx_sensor_readings_timestamp 
    ON sensor_readings(timestamp DESC);

-- Composite index for queries filtering by both
CREATE INDEX idx_sensor_readings_equipment_timestamp 
    ON sensor_readings(equipment_id, timestamp DESC);

-- Index for sensor type queries
CREATE INDEX idx_sensor_readings_type 
    ON sensor_readings(sensor_type);
```

**Migration Script:**

```python
def add_indexes(db_connection):
    """Add missing indexes to existing database"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_sensor_readings_equipment ON sensor_readings(equipment_id)",
        "CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_sensor_readings_equipment_timestamp ON sensor_readings(equipment_id, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_sensor_readings_type ON sensor_readings(sensor_type)"
    ]
    
    for index_sql in indexes:
        db_connection.execute(index_sql)
    
    db_connection.commit()
    print("Indexes created successfully")
```

**Key Principles:**
- Index columns used in WHERE clauses
- Index columns used in ORDER BY clauses
- Index foreign key columns
- Consider composite indexes for multi-column queries
- Balance index benefits vs. write performance cost
- Monitor index usage and remove unused indexes

### Validation

**Check Query Plan Before:**

```sql
EXPLAIN QUERY PLAN
SELECT * FROM sensor_readings 
WHERE equipment_id = 'PUMP-001' 
ORDER BY timestamp DESC 
LIMIT 10;

-- Output: SCAN sensor_readings
```

**Check Query Plan After:**

```sql
EXPLAIN QUERY PLAN
SELECT * FROM sensor_readings 
WHERE equipment_id = 'PUMP-001' 
ORDER BY timestamp DESC 
LIMIT 10;

-- Output: SEARCH sensor_readings USING INDEX idx_sensor_readings_equipment_timestamp
```

**Performance Comparison:**

| Rows in Table | Before (ms) | After (ms) | Speedup |
|--------------|-------------|------------|---------|
| 1,000        | 50          | 5          | 10x     |
| 10,000       | 200         | 8          | 25x     |
| 100,000      | 1,500       | 12         | 125x    |
| 1,000,000    | 15,000      | 15         | 1000x   |

---

## Performance Issue 3: Inefficient Algorithm Implementation

### Description

The statistics calculation method makes multiple passes over the sensor readings data, recalculating for each statistic instead of computing all statistics in a single pass.

### Location

**File**: `services/sensor_processor.py`  
**Method**: `SensorProcessor.calculate_statistics()`

### Hints for Discovery

1. Profile CPU usage during statistics calculation
2. Look for multiple iterations over the same data
3. Use AI tools:
   - "Find inefficient loops in this code"
   - "Optimize this statistics calculation"
4. Measure execution time with large datasets
5. Look for repeated list comprehensions

### Problematic Code Pattern

```python
class SensorProcessor:
    def calculate_statistics(self, readings: List[Dict]) -> Dict:
        # INEFFICIENT: Multiple passes over the data
        stats = {}
        
        # Pass 1: Calculate minimum
        stats['min'] = min([r['value'] for r in readings])
        
        # Pass 2: Calculate maximum
        stats['max'] = max([r['value'] for r in readings])
        
        # Pass 3: Calculate average
        stats['avg'] = sum([r['value'] for r in readings]) / len(readings)
        
        # Pass 4: Calculate count
        stats['count'] = len(readings)
        
        # Pass 5: Calculate standard deviation
        mean = stats['avg']
        variance = sum([(r['value'] - mean) ** 2 for r in readings]) / len(readings)
        stats['std_dev'] = variance ** 0.5
        
        return stats
```

### Performance Impact

**With 10,000 readings:**
- Current: 5 passes over data
- Time: ~150ms
- Memory: Multiple temporary lists created
- CPU: High due to repeated iterations

**Symptoms:**
- Slow statistics calculation
- High CPU usage when processing sensor data
- Increased memory allocation
- Poor scalability with data volume

### Remediation Guidance

**AI Prompts to Use:**
- "Optimize this statistics calculation to use a single pass"
- "Rewrite this to calculate all statistics in one loop"
- "Improve the performance of this data processing code"

**Optimized Implementation:**

```python
class SensorProcessor:
    def calculate_statistics(self, readings: List[Dict]) -> Dict:
        # OPTIMIZED: Single pass calculation
        if not readings:
            return {
                'min': None,
                'max': None,
                'avg': None,
                'count': 0,
                'std_dev': None
            }
        
        # Single pass through data
        min_val = float('inf')
        max_val = float('-inf')
        total = 0
        sum_squares = 0
        count = 0
        
        for reading in readings:
            value = reading['value']
            min_val = min(min_val, value)
            max_val = max(max_val, value)
            total += value
            sum_squares += value * value
            count += 1
        
        avg = total / count
        variance = (sum_squares / count) - (avg * avg)
        std_dev = variance ** 0.5 if variance > 0 else 0
        
        return {
            'min': min_val,
            'max': max_val,
            'avg': avg,
            'count': count,
            'std_dev': std_dev
        }
```

**Alternative: Using NumPy (if available):**

```python
import numpy as np

class SensorProcessor:
    def calculate_statistics(self, readings: List[Dict]) -> Dict:
        # OPTIMIZED: Using NumPy for vectorized operations
        if not readings:
            return {'min': None, 'max': None, 'avg': None, 'count': 0, 'std_dev': None}
        
        values = np.array([r['value'] for r in readings])
        
        return {
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'avg': float(np.mean(values)),
            'count': len(values),
            'std_dev': float(np.std(values))
        }
```

**Key Principles:**
- Minimize passes over data
- Combine operations when possible
- Use appropriate data structures
- Leverage optimized libraries (NumPy, Pandas)
- Avoid creating unnecessary temporary objects
- Consider algorithmic complexity (O(n) vs O(n²))

### Validation

**Performance Benchmark:**

```python
import time

# Generate test data
readings = [{'value': i * 0.1} for i in range(10000)]

# Test inefficient version
start = time.time()
stats_slow = sensor_processor_slow.calculate_statistics(readings)
time_slow = time.time() - start

# Test optimized version
start = time.time()
stats_fast = sensor_processor_fast.calculate_statistics(readings)
time_fast = time.time() - start

print(f"Slow version: {time_slow:.4f}s")
print(f"Fast version: {time_fast:.4f}s")
print(f"Speedup: {time_slow / time_fast:.1f}x")
```

**Performance Comparison:**

| Reading Count | Before (ms) | After (ms) | Speedup |
|--------------|-------------|------------|---------|
| 1,000        | 15          | 3          | 5x      |
| 10,000       | 150         | 25         | 6x      |
| 100,000      | 1,500       | 250        | 6x      |

---

## Performance Issue 4: Large API Payloads Without Pagination

### Description

The sensor readings API endpoint returns all matching records without pagination, potentially returning thousands of records in a single response.

### Location

**File**: `routes/api.py`  
**Endpoint**: `GET /api/sensors/readings`

### Hints for Discovery

1. Test API with large datasets
2. Monitor response sizes and times
3. Use AI tools:
   - "Find API endpoints that should implement pagination"
   - "Analyze this API for performance issues"
4. Check network traffic when querying sensor data
5. Look for endpoints that return unbounded result sets

### Problematic Code Pattern

```python
@app.route('/api/sensors/readings', methods=['GET'])
def get_sensor_readings():
    # INEFFICIENT: Returns ALL matching records
    equipment_id = request.args.get('equipment_id')
    sensor_type = request.args.get('sensor_type')
    
    # Could return thousands of records!
    readings = sensor_repo.get_readings(
        equipment_id=equipment_id,
        sensor_type=sensor_type
    )
    
    return jsonify(readings)
```

### Performance Impact

**With 50,000 sensor readings:**
- Response size: 5-10 MB
- Response time: 2-5 seconds
- Memory usage: High on both server and client
- Network bandwidth: Excessive

**Symptoms:**
- Slow API responses
- High memory usage
- Network timeouts
- Poor mobile experience
- Browser freezing when rendering large datasets

### Remediation Guidance

**AI Prompts to Use:**
- "Add pagination to this API endpoint"
- "Implement cursor-based pagination for this query"
- "Show me how to paginate large result sets"

**Optimized Implementation (Offset Pagination):**

```python
@app.route('/api/sensors/readings', methods=['GET'])
def get_sensor_readings():
    # OPTIMIZED: Implement pagination
    equipment_id = request.args.get('equipment_id')
    sensor_type = request.args.get('sensor_type')
    
    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    per_page = min(per_page, 1000)  # Cap at 1000
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get paginated results
    readings = sensor_repo.get_readings(
        equipment_id=equipment_id,
        sensor_type=sensor_type,
        limit=per_page,
        offset=offset
    )
    
    # Get total count for pagination metadata
    total = sensor_repo.count_readings(
        equipment_id=equipment_id,
        sensor_type=sensor_type
    )
    
    return jsonify({
        'data': readings,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })
```

**Repository Implementation:**

```python
class SensorDataRepository:
    def get_readings(self, equipment_id=None, sensor_type=None, 
                     limit=100, offset=0) -> List[Dict]:
        # Build query with pagination
        sql = "SELECT * FROM sensor_readings WHERE 1=1"
        params = []
        
        if equipment_id:
            sql += " AND equipment_id = ?"
            params.append(equipment_id)
        
        if sensor_type:
            sql += " AND sensor_type = ?"
            params.append(sensor_type)
        
        sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        return self.db.execute_query(sql, tuple(params))
    
    def count_readings(self, equipment_id=None, sensor_type=None) -> int:
        # Count total matching records
        sql = "SELECT COUNT(*) as count FROM sensor_readings WHERE 1=1"
        params = []
        
        if equipment_id:
            sql += " AND equipment_id = ?"
            params.append(equipment_id)
        
        if sensor_type:
            sql += " AND sensor_type = ?"
            params.append(sensor_type)
        
        result = self.db.execute_query(sql, tuple(params))
        return result[0]['count'] if result else 0
```

**Optimized Implementation (Cursor Pagination):**

```python
@app.route('/api/sensors/readings', methods=['GET'])
def get_sensor_readings():
    # OPTIMIZED: Cursor-based pagination (better for large datasets)
    equipment_id = request.args.get('equipment_id')
    sensor_type = request.args.get('sensor_type')
    cursor = request.args.get('cursor')  # Last seen timestamp
    per_page = int(request.args.get('per_page', 100))
    per_page = min(per_page, 1000)
    
    readings = sensor_repo.get_readings_cursor(
        equipment_id=equipment_id,
        sensor_type=sensor_type,
        cursor=cursor,
        limit=per_page
    )
    
    # Next cursor is the timestamp of the last item
    next_cursor = readings[-1]['timestamp'] if readings else None
    
    return jsonify({
        'data': readings,
        'pagination': {
            'next_cursor': next_cursor,
            'per_page': per_page,
            'has_more': len(readings) == per_page
        }
    })
```

**Key Principles:**
- Always paginate large result sets
- Provide reasonable default page sizes
- Cap maximum page size to prevent abuse
- Include pagination metadata in responses
- Consider cursor-based pagination for real-time data
- Document pagination parameters in API docs

### Validation

**Test Pagination:**

```bash
# Get first page
curl "http://localhost:5000/api/sensors/readings?page=1&per_page=100"

# Get second page
curl "http://localhost:5000/api/sensors/readings?page=2&per_page=100"

# Test with cursor
curl "http://localhost:5000/api/sensors/readings?cursor=2024-12-04T10:30:00&per_page=100"
```

**Performance Comparison:**

| Total Records | Before (MB) | After (MB) | Before (s) | After (s) |
|--------------|-------------|------------|------------|-----------|
| 1,000        | 1.0         | 0.1        | 0.5        | 0.05      |
| 10,000       | 10.0        | 0.1        | 3.0        | 0.05      |
| 100,000      | 100.0       | 0.1        | 25.0       | 0.05      |

---

## General Performance Best Practices

After addressing the specific issues, consider these additional optimizations:

### Database Optimization

- Use connection pooling
- Implement query result caching
- Use database transactions appropriately
- Analyze and optimize slow queries
- Consider read replicas for scaling

### Application Optimization

- Implement response caching (Redis, Memcached)
- Use asynchronous processing for heavy tasks
- Implement request rate limiting
- Optimize JSON serialization
- Use compression for API responses

### Monitoring and Profiling

- Implement application performance monitoring (APM)
- Log slow queries and requests
- Use profiling tools (cProfile, py-spy)
- Monitor database query patterns
- Track key performance metrics

### Code Quality

- Write performance tests
- Benchmark critical paths
- Use appropriate data structures
- Avoid premature optimization
- Profile before optimizing

## Workshop Exercise Checklist

Use this checklist to track your progress:

- [ ] Discovered N+1 query problem
- [ ] Fixed N+1 queries using JOINs
- [ ] Discovered missing database indexes
- [ ] Added appropriate indexes to schema
- [ ] Discovered inefficient statistics calculation
- [ ] Optimized algorithm to single-pass
- [ ] Discovered large API payloads
- [ ] Implemented pagination
- [ ] Measured performance improvements
- [ ] Verified optimizations with tests
- [ ] Documented lessons learned

## Performance Testing Tools

### Database Query Analysis

```python
# Enable SQLite query logging
import sqlite3

def trace_queries(statement):
    print(f"Executing: {statement}")

connection = sqlite3.connect('industrial_monitoring.db')
connection.set_trace_callback(trace_queries)
```

### Python Profiling

```python
import cProfile
import pstats

# Profile a function
profiler = cProfile.Profile()
profiler.enable()

# Your code here
result = sensor_processor.calculate_statistics(readings)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### API Performance Testing

```bash
# Use Apache Bench
ab -n 1000 -c 10 http://localhost:5000/api/sensors/readings

# Use wrk
wrk -t4 -c100 -d30s http://localhost:5000/api/sensors/readings
```

## Additional Resources

- [SQLite Query Optimization](https://www.sqlite.org/optoverview.html)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [Database Indexing Best Practices](https://use-the-index-luke.com/)
- [API Pagination Patterns](https://www.moesif.com/blog/technical/api-design/REST-API-Design-Filtering-Sorting-and-Pagination/)

---

**Remember**: These performance issues are intentional for educational purposes. Always profile and measure before optimizing in real applications!
