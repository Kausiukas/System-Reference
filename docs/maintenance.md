# Maintenance Guide

## Deployment

### System Requirements

- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space
- Internet connection for API access

### Production Deployment

1. **Environment Setup**:
```bash
# Create production environment
python -m venv venv_prod
source venv_prod/bin/activate  # On Windows: venv_prod\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configuration**:
```bash
# Copy and edit configuration
cp .env.example .env.prod
# Edit .env.prod with production settings
```

3. **Database Setup**:
```bash
# Initialize vector stores
python scripts/init_vector_stores.py

# Set up local knowledge base
python scripts/init_knowledge_base.py
```

4. **Service Configuration**:
```bash
# Set up systemd service (Linux)
sudo cp systemd/business-case-agent.service /etc/systemd/system/
sudo systemctl enable business-case-agent
sudo systemctl start business-case-agent

# Or use supervisor (cross-platform)
sudo cp supervisor/business-case-agent.conf /etc/supervisor/conf.d/
sudo supervisorctl update
sudo supervisorctl start business-case-agent
```

### Monitoring Setup

1. **Logging**:
```bash
# Configure logging
cp logging.conf.example logging.conf
# Edit logging.conf with desired settings
```

2. **Metrics**:
```bash
# Set up metrics collection
python scripts/setup_metrics.py

# Configure alerts
python scripts/configure_alerts.py
```

3. **Health Checks**:
```bash
# Set up health check endpoints
python scripts/setup_health_checks.py
```

## Configuration

### Environment Variables

```bash
# API Configuration
OPENAI_API_KEY=your_api_key
VECTOR_DB_PATH=/path/to/vector/db
MAX_DOCUMENT_SIZE=10485760  # 10MB

# Performance Settings
MAX_CONCURRENT_ANALYSIS=3
CACHE_SIZE=1000
RATE_LIMIT_PER_MINUTE=30

# Storage Settings
DOCUMENT_STORAGE_PATH=/path/to/documents
BACKUP_PATH=/path/to/backups
```

### Performance Tuning

1. **Memory Management**:
```python
# config/performance.py
MEMORY_LIMIT = 4 * 1024 * 1024 * 1024  # 4GB
CACHE_SIZE = 1000
BATCH_SIZE = 10
```

2. **Concurrency**:
```python
# config/concurrency.py
MAX_WORKERS = 3
THREAD_POOL_SIZE = 5
QUEUE_SIZE = 100
```

3. **Caching**:
```python
# config/cache.py
CACHE_TTL = 3600  # 1 hour
MAX_CACHE_SIZE = 1000
CACHE_CLEANUP_INTERVAL = 300  # 5 minutes
```

### Security Configuration

1. **Access Control**:
```python
# config/security.py
ALLOWED_IPS = ['127.0.0.1']
API_KEY_REQUIRED = True
RATE_LIMIT_ENABLED = True
```

2. **Data Protection**:
```python
# config/encryption.py
ENCRYPTION_KEY = 'your_encryption_key'
ENCRYPTION_ALGORITHM = 'AES-256-GCM'
```

## Update Procedures

### Regular Updates

1. **Backup**:
```bash
# Create backup
python scripts/backup.py

# Verify backup
python scripts/verify_backup.py
```

2. **Update Code**:
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade
```

3. **Database Migration**:
```bash
# Run migrations
python scripts/migrate_db.py

# Verify migration
python scripts/verify_migration.py
```

4. **Restart Services**:
```bash
# Restart service
sudo systemctl restart business-case-agent
# Or
sudo supervisorctl restart business-case-agent
```

### Emergency Updates

1. **Rollback Procedure**:
```bash
# Revert to previous version
git checkout <previous_version>

# Restore backup
python scripts/restore_backup.py

# Restart service
sudo systemctl restart business-case-agent
```

2. **Hot Fixes**:
```bash
# Apply hot fix
git checkout -b hotfix/<issue_number>
# Make changes
git commit -m "Hot fix: <issue_description>"
git push origin hotfix/<issue_number>
```

## Maintenance Tasks

### Daily Tasks

1. **Log Rotation**:
```bash
# Configure log rotation
sudo logrotate -f /etc/logrotate.d/business-case-agent
```

2. **Backup Verification**:
```bash
# Verify backups
python scripts/verify_backups.py
```

3. **Performance Check**:
```bash
# Check system performance
python scripts/check_performance.py
```

### Weekly Tasks

1. **Database Maintenance**:
```bash
# Optimize vector stores
python scripts/optimize_vector_stores.py

# Clean up old data
python scripts/cleanup_old_data.py
```

2. **Security Audit**:
```bash
# Run security checks
python scripts/security_audit.py
```

3. **Performance Analysis**:
```bash
# Generate performance report
python scripts/generate_performance_report.py
```

### Monthly Tasks

1. **System Update**:
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
pip install -r requirements.txt --upgrade
```

2. **Capacity Planning**:
```bash
# Analyze resource usage
python scripts/analyze_resource_usage.py

# Generate capacity report
python scripts/generate_capacity_report.py
```

3. **Documentation Update**:
```bash
# Update API documentation
python scripts/update_api_docs.py

# Update user guide
python scripts/update_user_guide.py
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**:
```bash
# Check logs
tail -f /var/log/business-case-agent.log

# Check system resources
python scripts/check_resources.py
```

2. **Performance Issues**:
```bash
# Check system load
python scripts/check_system_load.py

# Analyze bottlenecks
python scripts/analyze_bottlenecks.py
```

3. **Database Issues**:
```bash
# Check database health
python scripts/check_db_health.py

# Repair if needed
python scripts/repair_db.py
```

### Recovery Procedures

1. **Data Recovery**:
```bash
# Restore from backup
python scripts/restore_from_backup.py

# Verify data integrity
python scripts/verify_data_integrity.py
```

2. **Service Recovery**:
```bash
# Reset service state
python scripts/reset_service.py

# Verify service health
python scripts/verify_service_health.py
```

3. **Configuration Recovery**:
```bash
# Restore configuration
python scripts/restore_config.py

# Verify configuration
python scripts/verify_config.py
``` 