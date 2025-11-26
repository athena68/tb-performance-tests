# Quick Reference Card

## Plug & Play in 5 Minutes

### 1. Extract
```bash
unzip performance-tests-dist-4.0.1.zip
cd performance-tests-dist-4.0.1
```

### 2. Configure
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

### 3. Set Essentials
```bash
REST_URL=http://your-thingsboard:8080
REST_USERNAME=your_user
REST_PASSWORD=your_password
MQTT_HOST=your-mqtt-host
DEVICE_END_IDX=100
MESSAGES_PER_SECOND=50
```

### 4. Run
```bash
./run.sh          # Linux/macOS
run.bat           # Windows
```

### 5. Monitor
Watch ThingsBoard UI for devices and telemetry

---

## Common Commands

| Task | Command |
|------|---------|
| **Test Java** | `java -version` |
| **Extract** | `unzip performance-tests-dist-4.0.1.zip` |
| **Configure** | `cp .env.example .env && nano .env` |
| **Run (Linux)** | `./run.sh` |
| **Run (Windows)** | `run.bat` |
| **Direct run** | `source .env && java -jar *.jar` |
| **Check REST** | `curl -I http://your-server:8080` |
| **Check MQTT** | `nc -zv $MQTT_HOST 1883` |

---

## Key Configuration

```bash
# Connection
REST_URL=http://localhost:8080
REST_USERNAME=tenant@thingsboard.org
REST_PASSWORD=tenant
MQTT_HOST=localhost

# Test
TEST_PAYLOAD_TYPE=EBMPAPST_FFU        # FFU, SMART_METER, SMART_TRACKER, etc.
DEVICE_END_IDX=100                    # Number of devices
MESSAGES_PER_SECOND=50                # Rate
DURATION_IN_SECONDS=300               # 5 minutes
```

---

## Payload Types

| Type | Use Case |
|------|----------|
| **EBMPAPST_FFU** | Fan Filter Unit (default) |
| **SMART_METER** | Utility meters |
| **SMART_TRACKER** | GPS tracking |
| **INDUSTRIAL_PLC** | Industrial sensors |
| **DEFAULT** | Basic telemetry |

---

## Quick Test Scenarios

### Light Test
```bash
DEVICE_END_IDX=10
MESSAGES_PER_SECOND=5
DURATION_IN_SECONDS=60
```

### Standard Test
```bash
DEVICE_END_IDX=100
MESSAGES_PER_SECOND=50
DURATION_IN_SECONDS=300
```

### Heavy Test
```bash
DEVICE_END_IDX=1000
MESSAGES_PER_SECOND=100
DURATION_IN_SECONDS=300
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Java not found | Install Java 17+ |
| Connection refused | Check REST_URL, verify server running |
| MQTT error | Check MQTT_HOST, verify broker running |
| Credentials error | Verify REST_USERNAME and REST_PASSWORD |
| No devices created | Check DEVICE_CREATE_ON_START=true |
| No telemetry | Check TEST_PAYLOAD_TYPE matches scenario |

---

## Files in Package

| File | Purpose |
|------|---------|
| `tb-ce-performance-tests-4.0.1.jar` | Executable JAR (81 MB, all dependencies) |
| `run.sh` | Launcher for Linux/macOS |
| `run.bat` | Launcher for Windows |
| `.env.example` | Configuration template |
| `README.md` | Detailed guide |
| `PACKAGE.md` | Package details |
| `LICENSE` | Apache 2.0 License |

---

## System Requirements

- **Java**: 17+
- **RAM**: 2 GB minimum
- **Disk**: 150 MB
- **Network**: Connection to ThingsBoard

---

## Verification

```bash
# Check package integrity
sha256sum -c performance-tests-dist-4.0.1.zip.sha256
# Expected: f3a3662534d6d95b0e408f2e095d4a200fff39d924460be69d2c207a714f0ce1
```

---

## Environment Variables

All configuration via `.env` file. Key variables:

```bash
# Connection
REST_URL
REST_USERNAME
REST_PASSWORD
MQTT_HOST
MQTT_PORT

# Testing
TEST_API                    # device or gateway
TEST_PAYLOAD_TYPE          # Device type
DEVICE_API                 # MQTT, HTTP, LWM2M
DEVICE_START_IDX
DEVICE_END_IDX
MESSAGES_PER_SECOND
DURATION_IN_SECONDS

# Lifecycle
DEVICE_CREATE_ON_START     # true/false
DEVICE_DELETE_ON_COMPLETE  # true/false
WARMUP_ENABLED             # true/false
```

---

## Performance Tips

1. **Start small**: Test with 10 devices first
2. **Gradual increase**: Double load every test
3. **Monitor**: Watch server during test
4. **Network**: Ensure good bandwidth
5. **Cleanup**: Delete test devices after testing

---

## Next: Full Documentation

See `DEPLOYMENT_GUIDE.md` for:
- Detailed setup instructions
- Configuration reference
- Troubleshooting guide
- Performance tuning
- Example scenarios

---

**Version**: 4.0.1 | **License**: Apache 2.0 | **Date**: Nov 25, 2025
