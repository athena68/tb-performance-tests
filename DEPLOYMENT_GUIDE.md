# ThingsBoard Performance Tests - Deployment Guide

## Overview

Complete plug-and-play distribution package for ThingsBoard performance testing. No build tools required on target machines.

**Package**: `performance-tests-dist-4.0.1.zip`
**Size**: 73 MB
**SHA256**: `f3a3662534d6d95b0e408f2e095d4a200fff39d924460be69d2c207a714f0ce1`

## What's Included

```
performance-tests-dist-4.0.1/
├── tb-ce-performance-tests-4.0.1.jar    # Executable JAR (81MB, all deps)
├── run.sh                               # Launcher script (Linux/macOS)
├── run.bat                              # Launcher script (Windows)
├── .env.example                         # Configuration template
├── README.md                            # Quick start guide
├── CHANGELOG.md                         # Version history
├── LICENSE                              # Apache 2.0 License
└── PACKAGE.md                           # Package details
```

## System Requirements

| Component | Requirement |
|-----------|------------|
| **Java** | 17 or higher |
| **RAM** | 2 GB minimum (4+ GB recommended) |
| **Storage** | 150 MB free space (for extraction and temp files) |
| **Network** | Access to ThingsBoard server and MQTT broker |
| **OS** | Linux, macOS, Windows |

## Installation & Setup

### Step 1: Extract Package

**Linux/macOS:**
```bash
unzip performance-tests-dist-4.0.1.zip
cd performance-tests-dist-4.0.1
```

**Windows:**
- Right-click ZIP file → Extract All
- Navigate to the extracted folder

### Step 2: Verify Java

```bash
java -version
```

**Expected output**: Java 17 or higher

**If Java is not installed:**

- **Ubuntu/Debian**: `sudo apt install openjdk-17-jre-headless`
- **CentOS/RHEL**: `sudo yum install java-17-openjdk`
- **macOS**: `brew install openjdk@17`
- **Windows**: Download from [Adoptium](https://adoptium.net/)

### Step 3: Configure

```bash
# Copy configuration template
cp .env.example .env

# Edit configuration
nano .env          # Linux/macOS
notepad .env       # Windows (or any text editor)
```

### Step 4: Essential Settings

Edit `.env` and set these required variables:

```bash
# ThingsBoard Connection
REST_URL=http://your-thingsboard-server:8080
REST_USERNAME=your_username
REST_PASSWORD=your_password

# MQTT Settings
MQTT_HOST=your-mqtt-host
MQTT_PORT=1883

# Test Parameters
TEST_PAYLOAD_TYPE=EBMPAPST_FFU          # Or SMART_METER, SMART_TRACKER, etc.
DEVICE_END_IDX=100                      # Number of devices
MESSAGES_PER_SECOND=50                  # Publishing rate
DURATION_IN_SECONDS=300                 # Test duration (5 minutes)
```

### Step 5: Run Tests

**Option A - Using launcher script (Recommended):**

```bash
# Linux/macOS
./run.sh

# Windows
run.bat
```

**Option B - Direct Java:**

```bash
source .env      # Linux/macOS
java -jar tb-ce-performance-tests-4.0.1.jar
```

## Configuration Reference

### Connection Parameters

| Variable | Default | Description |
|----------|---------|------------|
| `REST_URL` | http://localhost:8080 | ThingsBoard REST API |
| `REST_USERNAME` | tenant@thingsboard.org | Login username |
| `REST_PASSWORD` | tenant | Login password |
| `MQTT_HOST` | localhost | MQTT broker address |
| `MQTT_PORT` | 1883 | MQTT port |

### Test Parameters

| Variable | Default | Description |
|----------|---------|------------|
| `TEST_PAYLOAD_TYPE` | EBMPAPST_FFU | Device type: EBMPAPST_FFU, SMART_METER, SMART_TRACKER, INDUSTRIAL_PLC, DEFAULT |
| `DEVICE_API` | MQTT | Protocol: MQTT, HTTP, LWM2M |
| `TEST_API` | device | Mode: device (direct) or gateway |
| `DEVICE_START_IDX` | 0 | First device ID |
| `DEVICE_END_IDX` | 100 | Last device ID (count = END - START) |
| `MESSAGES_PER_SECOND` | 50 | Publishing rate |
| `DURATION_IN_SECONDS` | 300 | Test duration |
| `WARMUP_ENABLED` | true | Enable warmup phase |

### Lifecycle Options

| Variable | Default | Description |
|----------|---------|------------|
| `DEVICE_CREATE_ON_START` | true | Auto-create devices before test |
| `DEVICE_DELETE_ON_COMPLETE` | false | Auto-delete devices after test |
| `UPDATE_ROOT_RULE_CHAIN` | false | Replace root rule chain |
| `REVERT_ROOT_RULE_CHAIN` | false | Restore original rule chain |

### Alarm Settings

| Variable | Default | Description |
|----------|---------|------------|
| `ALARMS_PER_SECOND` | 0 | Alarm generation rate |

## Usage Examples

### Example 1: Light Load Test

Simulate 50 devices publishing 10 messages/second for 1 hour:

```bash
# .env configuration
DEVICE_END_IDX=50
MESSAGES_PER_SECOND=10
DURATION_IN_SECONDS=3600
TEST_PAYLOAD_TYPE=EBMPAPST_FFU
```

### Example 2: Medium Load Test

Simulate 500 devices publishing 30 messages/second for 10 minutes:

```bash
DEVICE_END_IDX=500
MESSAGES_PER_SECOND=30
DURATION_IN_SECONDS=600
TEST_PAYLOAD_TYPE=SMART_METER
```

### Example 3: Heavy Load Test

Simulate 2000 devices publishing 100 messages/second for 5 minutes:

```bash
DEVICE_END_IDX=2000
MESSAGES_PER_SECOND=100
DURATION_IN_SECONDS=300
DEVICE_CREATE_ON_START=false      # Pre-created devices
WARMUP_ENABLED=true
```

### Example 4: Gateway Test

Simulate 100 devices through a gateway:

```bash
TEST_API=gateway
DEVICE_END_IDX=100
MESSAGES_PER_SECOND=50
DURATION_IN_SECONDS=300
```

## Output & Monitoring

The application displays:

```
==========================================
ThingsBoard Performance Tests
==========================================
Java Version: 17
JAR File: tb-ce-performance-tests-4.0.1.jar

Configuration:
  REST_URL: http://localhost:8080
  MQTT_HOST: localhost
  TEST_PAYLOAD_TYPE: EBMPAPST_FFU
  DEVICE_END_IDX: 100
  MESSAGES_PER_SECOND: 50

Starting performance tests...
==========================================

[INFO] Initializing test...
[INFO] Authenticating to ThingsBoard...
[INFO] Creating device profile...
[INFO] Creating 100 devices...
[INFO] Starting warmup (10 seconds)...
[INFO] Beginning test phase...
[INFO] Published: 5000 messages | Success: 4998 | Failed: 2
[INFO] Throughput: 49.8 msg/sec
[INFO] Test complete!
[INFO] Cleaning up...
```

## Troubleshooting

### Error: "Java is not installed"

**Solution:**
```bash
# Verify Java installation
which java
java -version

# If not installed, install Java 17
```

### Error: "Connection refused"

```bash
# Check REST endpoint is reachable
curl -I http://your-server:8080

# Check credentials
curl -u username:password http://your-server:8080/api/auth/login
```

### Error: "MQTT connection failed"

```bash
# Test MQTT connectivity
nc -zv $MQTT_HOST $MQTT_PORT

# Or use netcat alternative
timeout 2 bash -c 'cat < /dev/null > /dev/tcp/$MQTT_HOST/$MQTT_PORT'
```

### No devices appear in ThingsBoard

1. Check `DEVICE_CREATE_ON_START=true` in `.env`
2. Verify REST credentials have admin privileges
3. Check ThingsBoard server logs
4. Increase `LOGGING_LEVEL=DEBUG` for detailed output

### Low throughput

1. Check network bandwidth: `iperf3 -c $MQTT_HOST`
2. Monitor server resources: `top` or Windows Task Manager
3. Reduce `MESSAGES_PER_SECOND` initially
4. Check firewall rules

### Devices created but no telemetry

1. Verify `TEST_PAYLOAD_TYPE` matches your scenario
2. Check device connectivity in ThingsBoard UI
3. Review rule chain configuration
4. Check attribute mappings for FFU payloads

## Performance Tuning

### For Maximum Throughput

```bash
DEVICE_END_IDX=10000
MESSAGES_PER_SECOND=500
DURATION_IN_SECONDS=300
DEVICE_CREATE_ON_START=false
WARMUP_ENABLED=false
```

### For Stability Testing

```bash
DEVICE_END_IDX=1000
MESSAGES_PER_SECOND=50
DURATION_IN_SECONDS=3600        # 1 hour
WARMUP_ENABLED=true
```

### For Gateway Testing

```bash
TEST_API=gateway
DEVICE_END_IDX=500
MESSAGES_PER_SECOND=100
DURATION_IN_SECONDS=600
```

## Verification Checklist

Before running production tests:

- [ ] Java 17+ installed: `java -version`
- [ ] ThingsBoard server running
- [ ] MQTT broker accessible
- [ ] Correct credentials in `.env`
- [ ] Adequate disk space (100+ MB)
- [ ] Network connectivity verified
- [ ] Test with small load first (10 devices)
- [ ] Monitor ThingsBoard during test
- [ ] Check application logs for errors

## File Integrity

Verify package integrity using SHA256:

```bash
# Linux/macOS
sha256sum -c performance-tests-dist-4.0.1.zip.sha256

# Or manually
sha256sum performance-tests-dist-4.0.1.zip
# Compare with: f3a3662534d6d95b0e408f2e095d4a200fff39d924460be69d2c207a714f0ce1

# Windows (PowerShell)
Get-FileHash performance-tests-dist-4.0.1.zip -Algorithm SHA256
```

## Updating Configuration

Edit `.env` at any time. The application loads configuration on startup.

```bash
# Edit configuration
nano .env

# Run with updated settings
./run.sh
```

## Support & Troubleshooting

1. **Check README.md** - Included in package
2. **Check PACKAGE.md** - Package structure details
3. **Review logs** - Application prints detailed logs to console
4. **Monitor server** - Check ThingsBoard UI for device status

## Performance Metrics

The tool measures:

- **Throughput**: Messages published per second
- **Success Rate**: Percentage of successful publishes
- **Connection Count**: Number of connected devices
- **Message Latency**: Time from publish to ThingsBoard
- **Error Rate**: Failed messages

## Next Steps

1. Extract `performance-tests-dist-4.0.1.zip`
2. Verify Java 17+ installed
3. Copy `.env.example` → `.env`
4. Update `.env` with your settings
5. Run `./run.sh`
6. Monitor results in ThingsBoard

---

**Version**: 4.0.1
**Built**: November 25, 2025
**License**: Apache 2.0
**Repository**: ThingsBoard Performance Tests
