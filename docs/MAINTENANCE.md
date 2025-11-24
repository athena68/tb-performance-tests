# Maintenance Guide

## Overview

This guide provides procedures for maintaining the ThingsBoard Performance Tests project, including cleanup, troubleshooting, and regular maintenance tasks.

## Regular Maintenance Tasks

### 1. Cleanup Devices and Assets

#### Full Cleanup (All Entities)

```bash
python3 test-scenarios/cleanup-scenario.py \
  --credentials test-scenarios/credentials.json \
  --assets \
  --devices \
  --confirm
```

**What it does**:
- Deletes all customer assets
- Deletes all customer devices (including gateways)
- Requires explicit `--confirm` flag for safety

#### Devices Only

```bash
python3 test-scenarios/cleanup-scenario.py \
  --credentials test-scenarios/credentials.json \
  --devices \
  --confirm
```

#### Assets Only

```bash
python3 test-scenarios/cleanup-scenario.py \
  --credentials test-scenarios/credentials.json \
  --assets \
  --confirm
```

### 2. Cleanup Build Artifacts

```bash
# Remove Maven build artifacts
mvn clean

# Remove Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove log files
rm -f *.log

# Remove backup files
find . -type f -name "*.bak" -delete
```

### 3. Reset Test Environment

```bash
# 1. Clean up ThingsBoard
python3 test-scenarios/cleanup-scenario.py \
  --credentials test-scenarios/credentials.json \
  --assets --devices --confirm

# 2. Re-provision from scratch
python3 test-scenarios/provision-scenario.py \
  test-scenarios/scenario-hanoi-cleanroom.json \
  --credentials test-scenarios/credentials.json

# 3. Verify .env was generated
cat .env

# 4. Run performance test
source .env && mvn spring-boot:run
```

## Troubleshooting

### Issue: Provision Script Hangs

**Symptoms**: Script appears to hang during device creation

**Causes**:
1. ThingsBoard server not responding
2. Network timeout
3. Device limit reached

**Solutions**:
```bash
# 1. Check ThingsBoard server status
curl -s http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}'

# 2. Check device count
python3 -c "
import requests
import json
r = requests.post('http://localhost:8080/api/auth/login',
  json={'username':'tenant@thingsboard.org','password':'tenant'})
token = r.json()['token']
r = requests.get('http://localhost:8080/api/tenant/devices?pageSize=1000&page=0',
  headers={'X-Authorization': f'Bearer {token}'})
print(f'Total devices: {len(r.json()[\"data\"])}')
"

# 3. Increase timeout in provision script (if needed)
# Edit test-scenarios/provision-scenario.py
# Change HTTP_TIMEOUT from 30 to 60 seconds
```

### Issue: Java App MQTT Connection Failure

**Symptoms**: "Failed to connect to MQTT broker at localhost:1883"

**Causes**:
1. ThingsBoard MQTT transport not running
2. Incorrect MQTT host/port
3. Firewall blocking port 1883

**Solutions**:
```bash
# 1. Check if port 1883 is open
nc -zv localhost 1883

# 2. Check ThingsBoard logs
tail -f /var/log/thingsboard/thingsboard.log | grep -i mqtt

# 3. Verify MQTT configuration in .env
grep MQTT .env

# 4. Test MQTT connection manually
mosquitto_pub -h localhost -p 1883 \
  -u "GW00000000" \
  -t "v1/gateway/telemetry" \
  -m '{"test": 1}'
```

### Issue: Wrong Device Credentials

**Symptoms**: Devices exist but Java app can't connect

**Solutions**:
```bash
# Re-run provision script to update credentials
python3 test-scenarios/provision-scenario.py \
  test-scenarios/scenario-hanoi-cleanroom.json \
  --credentials test-scenarios/credentials.json

# This will:
# 1. Detect existing devices
# 2. Update their credentials to match device names
# 3. Regenerate .env file
```

### Issue: Incorrect .env Configuration

**Symptoms**: Java app uses wrong device ranges or payload type

**Solutions**:
```bash
# 1. Delete old .env
rm .env

# 2. Regenerate from provision script
python3 test-scenarios/provision-scenario.py \
  test-scenarios/scenario-hanoi-cleanroom.json \
  --credentials test-scenarios/credentials.json

# 3. Verify configuration
cat .env | grep -E "(DEVICE_|GATEWAY_|PAYLOAD)"
```

## Performance Optimization

### Database Cleanup

ThingsBoard accumulates telemetry data over time. Regular cleanup improves performance:

```bash
# Via ThingsBoard UI:
# 1. System Settings → General Settings
# 2. Configure TTL for telemetry data
# 3. Set reasonable retention periods

# Or via SQL (PostgreSQL):
# DELETE FROM ts_kv WHERE ts < NOW() - INTERVAL '30 days';
```

### Java App Performance

```bash
# Increase heap size for large tests
export MAVEN_OPTS="-Xmx4g -Xms2g"
mvn spring-boot:run

# Or use compiled JAR for better performance
mvn clean package -DskipTests
java -Xmx4g -jar target/tb-ce-performance-test-*.jar
```

## Backup and Recovery

### Backup Configuration

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup scenarios
cp test-scenarios/*.json backups/$(date +%Y%m%d)/

# Backup attributes
cp -r config/attributes backups/$(date +%Y%m%d)/

# Backup credentials (IMPORTANT: Keep secure!)
cp test-scenarios/credentials.json backups/$(date +%Y%m%d)/

# Create archive
tar czf backups/backup-$(date +%Y%m%d).tar.gz backups/$(date +%Y%m%d)/
```

### Recovery from Backup

```bash
# Extract backup
tar xzf backups/backup-20250124.tar.gz

# Restore files
cp backups/20250124/*.json test-scenarios/
cp -r backups/20250124/attributes config/
cp backups/20250124/credentials.json test-scenarios/

# Re-provision
python3 test-scenarios/provision-scenario.py \
  test-scenarios/scenario-hanoi-cleanroom.json \
  --credentials test-scenarios/credentials.json
```

## Monitoring

### Check Device Status

```bash
# Via Python script
python3 << 'EOF'
import requests
import json

# Login
r = requests.post('http://localhost:8080/api/auth/login',
  json={'username':'tenant@thingsboard.org','password':'tenant'})
token = r.json()['token']

# Get devices
r = requests.get('http://localhost:8080/api/tenant/devices?pageSize=1000&page=0',
  headers={'X-Authorization': f'Bearer {token}'})

devices = r.json()['data']
print(f"Total devices: {len(devices)}")
print(f"Gateways: {sum(1 for d in devices if d['type'] == 'Gateway')}")
print(f"FFU Devices: {sum(1 for d in devices if d['type'] == 'EBMPAPST_FFU')}")
EOF
```

### Monitor Test Progress

```bash
# Watch Java app logs
tail -f /tmp/java-test.log | grep -E "(Connected|Publishing|Error)"

# Monitor ThingsBoard server
tail -f /var/log/thingsboard/thingsboard.log | grep -E "(gateway|device|telemetry)"
```

## Security Best Practices

### Credentials Management

```bash
# NEVER commit credentials to git
echo "test-scenarios/credentials.json" >> .gitignore

# Use restrictive permissions
chmod 600 test-scenarios/credentials.json

# Rotate credentials regularly
# Update credentials.json and re-provision
```

### Network Security

```bash
# Use TLS for production deployments
# Update .env:
MQTT_SSL_ENABLED=true
REST_URL=https://thingsboard.example.com

# Use strong passwords
# Avoid default credentials in production
```

## Git Repository Maintenance

### Cleanup Uncommitted Changes

```bash
# View changes
git status

# Discard changes to modified files
git checkout -- <file>

# Remove untracked files (be careful!)
git clean -fd

# Reset to clean state
git reset --hard HEAD
```

### Update from Remote

```bash
# Fetch latest changes
git fetch origin

# View differences
git diff HEAD origin/main

# Merge changes
git pull origin main
```

## Health Checks

### Quick Health Check Script

```bash
#!/bin/bash
# save as check-health.sh

echo "=== ThingsBoard Performance Tests Health Check ==="
echo ""

# 1. Check ThingsBoard server
echo "1. Checking ThingsBoard server..."
if curl -s http://localhost:8080/api/auth/login > /dev/null 2>&1; then
  echo "   ✓ ThingsBoard server is accessible"
else
  echo "   ✗ ThingsBoard server is not accessible"
fi

# 2. Check MQTT port
echo "2. Checking MQTT port..."
if nc -zv localhost 1883 > /dev/null 2>&1; then
  echo "   ✓ MQTT port 1883 is open"
else
  echo "   ✗ MQTT port 1883 is not accessible"
fi

# 3. Check Python dependencies
echo "3. Checking Python dependencies..."
if python3 -c "import requests, yaml, json" > /dev/null 2>&1; then
  echo "   ✓ Python dependencies installed"
else
  echo "   ✗ Missing Python dependencies"
fi

# 4. Check Java
echo "4. Checking Java..."
if java -version > /dev/null 2>&1; then
  echo "   ✓ Java is installed"
else
  echo "   ✗ Java is not installed"
fi

# 5. Check credentials file
echo "5. Checking credentials..."
if [ -f test-scenarios/credentials.json ]; then
  echo "   ✓ Credentials file exists"
else
  echo "   ✗ Credentials file missing"
fi

echo ""
echo "=== Health Check Complete ==="
```

## Scheduled Maintenance

### Weekly Tasks
- [ ] Review ThingsBoard logs for errors
- [ ] Check disk space usage
- [ ] Backup configuration files
- [ ] Review device count and clean up if needed

### Monthly Tasks
- [ ] Update dependencies (`mvn versions:display-dependency-updates`)
- [ ] Review and optimize test scenarios
- [ ] Clean up old telemetry data
- [ ] Update documentation

### Quarterly Tasks
- [ ] Performance benchmarking
- [ ] Security audit
- [ ] Review and update architecture documentation
- [ ] Evaluate new ThingsBoard features
