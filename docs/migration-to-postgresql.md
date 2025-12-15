# Migration Guide: SQLite to PostgreSQL

This guide provides a comprehensive, step-by-step approach to migrating the idea-planner-agent from SQLite to PostgreSQL, ensuring minimal downtime and data integrity.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Key Differences Between SQLite and PostgreSQL](#key-differences-between-sqlite-and-postgresql)
- [Migration Strategy](#migration-strategy)
- [Step 1: Prepare PostgreSQL Environment](#step-1-prepare-postgresql-environment)
- [Step 2: Update Database Configuration](#step-2-update-database-configuration)
- [Step 3: Schema Migration](#step-3-schema-migration)
- [Step 4: Data Migration](#step-4-data-migration)
- [Step 5: Application Code Updates](#step-5-application-code-updates)
- [Step 6: Testing and Validation](#step-6-testing-and-validation)
- [Step 7: Deployment and Cutover](#step-7-deployment-and-cutover)
- [Troubleshooting](#troubleshooting)
- [Rollback Plan](#rollback-plan)

## Prerequisites

Before starting the migration, ensure you have:

- PostgreSQL server (version 12+) installed and running
- `psql` command-line client installed
- Python packages: `psycopg2-binary`, `pg_dump`, `pg_restore`
- Backup of your current SQLite database (`bot.db`)
- Access to modify application configuration and code

```bash
# Install required packages
pip install psycopg2-binary
```

## Key Differences Between SQLite and PostgreSQL

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Database Type** | File-based | Client-server |
| **Concurrency** | Limited (file locking) | Excellent (MVCC) |
| **Data Types** | Flexible typing | Strict typing |
| **Performance** | Good for small workloads | Excellent for concurrent workloads |
| **Scalability** | Limited | Highly scalable |
| **Connection Handling** | Simple | Connection pooling recommended |

## Migration Strategy

The migration follows a **dual-write approach** to ensure data integrity:

1. **Phase 1**: Set up PostgreSQL alongside SQLite (read from SQLite, write to both)
2. **Phase 2**: Backfill historical data to PostgreSQL
3. **Phase 3**: Switch reads to PostgreSQL (verify data consistency)
4. **Phase 4**: Decommission SQLite

## Step 1: Prepare PostgreSQL Environment

### 1.1 Install and Configure PostgreSQL

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# On macOS (using Homebrew)
brew install postgresql
brew services start postgresql
```

### 1.2 Create Database and User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE idea_planner;
CREATE USER planner_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE idea_planner TO planner_user;

# Connect to the new database
\c idea_planner

# Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 1.3 Configure PostgreSQL for Production

Edit `postgresql.conf`:
```ini
listen_addresses = '*'
max_connections = 100
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 16MB
maintenance_work_mem = 256MB
```

Edit `pg_hba.conf`:
```ini
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

## Step 2: Update Database Configuration

### 2.1 Modify `src/database.py`

Update the database connection string:

```python
# Change from:
engine = create_engine('sqlite:///bot.db', echo=False)

# To:
DATABASE_URL = "postgresql://planner_user:secure_password@localhost/idea_planner"
engine = create_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
```

### 2.2 Add Environment Configuration

Create a `.env` file:
```ini
DATABASE_URL=postgresql://planner_user:secure_password@localhost/idea_planner
```

Update `src/database.py` to use environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")
engine = create_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
```

## Step 3: Schema Migration

### 3.1 Generate SQLAlchemy Schema for PostgreSQL

SQLAlchemy handles most schema differences automatically, but some manual adjustments are needed:

```python
# Add this to your models for PostgreSQL-specific features
from sqlalchemy.dialects.postgresql import JSONB, UUID

# Example: Adding UUID support
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    # Add UUID column for PostgreSQL
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    # ... rest of your columns
```

### 3.2 Create Tables in PostgreSQL

```bash
# Run your application to create tables
python -c "from src.database import init_db; init_db()"

# Or manually create tables using SQLAlchemy
python -c "
from src.database import Base, engine
Base.metadata.create_all(engine)
"
```

## Step 4: Data Migration

### 4.1 Export Data from SQLite

```bash
# Export SQLite data to SQL format
sqlite3 bot.db .dump > sqlite_dump.sql

# Convert SQLite dump to PostgreSQL format
sed -i 's/AUTOINCREMENT/ /g' sqlite_dump.sql
sed -i 's/"users"/users/g' sqlite_dump.sql
sed -i 's/"ideas"/ideas/g' sqlite_dump.sql
sed -i 's/"analyses"/analyses/g' sqlite_dump.sql
```

### 4.2 Import Data to PostgreSQL

```bash
# Use pgloader for automated migration
pgloader sqlite:///bot.db postgresql://planner_user:secure_password@localhost/idea_planner

# Or use manual import
psql -U planner_user -d idea_planner -f sqlite_dump.sql
```

### 4.3 Verify Data Integrity

```python
# Create a verification script
import sqlite3
from sqlalchemy import create_engine

def verify_migration():
    # Connect to both databases
    sqlite_conn = sqlite3.connect('bot.db')
    pg_engine = create_engine('postgresql://planner_user:secure_password@localhost/idea_planner')
    
    # Compare record counts
    for table in ['users', 'ideas', 'analyses']:
        sqlite_count = sqlite_conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        pg_count = pg_engine.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        
        print(f"{table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
        assert sqlite_count == pg_count, f"Count mismatch for {table}"

if __name__ == "__main__":
    verify_migration()
```

## Step 5: Application Code Updates

### 5.1 Update Connection Pooling

```python
# Update engine creation for better PostgreSQL performance
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### 5.2 Handle PostgreSQL-Specific Features

```python
# Add transaction handling for critical operations
from contextlib import contextmanager

@contextmanager
def transaction_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

### 5.3 Update Enum Handling

```python
# PostgreSQL has better enum support
from sqlalchemy.dialects.postgresql import ENUM

# Create enum types for PostgreSQL
analysis_status_enum = ENUM(
    AnalysisStatus,
    name="analysis_status",
    create_type=True
)

analysis_mode_enum = ENUM(
    AnalysisMode,
    name="analysis_mode",
    create_type=True
)

# Update your model columns
class Analysis(Base):
    status = Column(analysis_status_enum, default=AnalysisStatus.QUEUED)
    
class Idea(Base):
    mode = Column(analysis_mode_enum, default=AnalysisMode.EVALUATION)
```

## Step 6: Testing and Validation

### 6.1 Create Comprehensive Test Suite

```python
# Add PostgreSQL-specific tests
import pytest
from src.database import User, Idea, Analysis, SessionLocal

def test_postgresql_connection():
    session = SessionLocal()
    assert session.bind.dialect.name == 'postgresql'
    session.close()

def test_data_integrity():
    session = SessionLocal()
    
    # Test user creation
    user = User(telegram_id="test_user", username="test")
    session.add(user)
    session.commit()
    
    # Test relationships
    idea = Idea(user_id=user.id, text="Test idea")
    session.add(idea)
    session.commit()
    
    # Verify data
    retrieved_user = session.query(User).filter_by(telegram_id="test_user").first()
    assert retrieved_user is not None
    assert len(retrieved_user.ideas) == 1
    
    session.close()
```

### 6.2 Performance Testing

```python
# Test concurrent connections
import threading
import time

def test_concurrent_operations():
    def worker():
        session = SessionLocal()
        try:
            user = User(telegram_id=f"user_{threading.current_thread().ident}")
            session.add(user)
            session.commit()
        finally:
            session.close()
    
    threads = []
    for i in range(50):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
```

## Step 7: Deployment and Cutover

### 7.1 Blue-Green Deployment Strategy

1. **Deploy new version** with PostgreSQL support alongside existing SQLite version
2. **Route 10% of traffic** to PostgreSQL version for testing
3. **Monitor performance** and error rates
4. **Gradually increase traffic** to 100% over 24-48 hours
5. **Decommission SQLite** after successful migration

### 7.2 Final Cutover Checklist

- [ ] Database backups verified
- [ ] All tests passing in staging
- [ ] Performance metrics acceptable
- [ ] Monitoring in place
- [ ] Rollback plan tested
- [ ] Team notified of migration window

## Troubleshooting

### Common Issues and Solutions

**Issue: Connection Timeouts**
```ini
# Increase connection pool settings
pool_size=20
max_overflow=40
pool_timeout=60
```

**Issue: Character Encoding Problems**
```sql
# Set proper encoding in PostgreSQL
ALTER DATABASE idea_planner SET client_encoding TO 'UTF8';
```

**Issue: Serial vs BigSerial**
```python
# Use BigInteger for large datasets
id = Column(BigInteger, primary_key=True)
```

**Issue: Case Sensitivity**
```sql
# PostgreSQL is case-sensitive for identifiers
-- Use double quotes for case-sensitive names
SELECT "UserName" FROM users;
```

## Rollback Plan

### Immediate Rollback Procedure

1. **Stop application traffic** to PostgreSQL version
2. **Restore SQLite database** from backup
3. **Revert configuration** to point to SQLite
4. **Restart application** with SQLite
5. **Investigate migration failure**

### Data Recovery

```bash
# Restore from PostgreSQL backup
pg_restore -U planner_user -d idea_planner -c -Fc backup.dump

# Export data back to SQLite
pg_dump -U planner_user idea_planner | sqlite3 restored.db
```

## Post-Migration Optimization

### Index Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_ideas_user_id ON ideas(user_id);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
```

### Query Optimization

```python
# Use eager loading for relationships
from sqlalchemy.orm import joinedload

# Optimized query
user = session.query(User).options(
    joinedload(User.ideas).joinedload(Idea.analyses)
).filter(User.id == user_id).first()
```

### Monitoring Setup

```python
# Add database monitoring
from sqlalchemy import event

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 1.0:  # Log slow queries
        print(f"Slow query: {total:.3f}s - {statement}")
```

## Conclusion

This migration guide provides a comprehensive path from SQLite to PostgreSQL, ensuring data integrity, minimal downtime, and improved scalability. The migration aligns with the original architecture decision to use SQLite initially with an easy migration path to PostgreSQL when needed.

**Key Benefits of PostgreSQL Migration:**
- Improved concurrency handling for growing user base
- Better performance under load
- Advanced features (JSONB, full-text search, etc.)
- Production-grade reliability and monitoring

**Estimated Migration Time:** 2-4 hours for development, 1-2 hours for production cutover with proper testing.