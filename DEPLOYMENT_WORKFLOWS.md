# Deployment Workflows

This document explains the two different ways to use the performance tests package.

## Overview

There are **two distinct workflows** depending on whether you have the provisioning scripts or just the JAR package.

---

## Workflow 1: With Provisioning Scripts (Recommended)

**Best for**: Full repository setup with automated device creation

### What You Need
- Full repository clone (with `test-scenarios/` directory)
- Python 3.8+
- ThingsBoard server access

### Setup Process

```bash
# 1. Clone or extract full repository
cd /path/to/performance-tests

# 2. Create credentials file
cat > test-scenarios/credentials.json << EOF
{
  "url": "http://your-server:8080",
  "username": "tenant@thingsboard.org",
  "password": "tenant"
}
EOF

# 3. Run provisioning script
python3 test-scenarios/provision-scenario.py \
  test-scenarios/scenario-hanoi-cleanroom.json \
  --credentials test-scenarios/credentials.json
```

### What Provisioning Does

1. **Connects to ThingsBoard** using credentials
2. **Creates entities**:
   - Sites (assets)
   - Buildings (assets)
   - Gateways (devices)
   - End devices (devices)
3. **Sets up relationships**:
   - Gateway → Device relations
   - Asset hierarchy
4. **Generates `.env` file** automatically with:
   - Device tokens
   - Gateway tokens
   - MQTT settings
   - Test configuration

### Running Tests

```bash
# .env is already created by provisioning
source .env && mvn spring-boot:run

# Or with the distributed JAR:
source .env && java -jar tb-ce-performance-tests-4.0.1.jar

# Or use the launcher:
./run.sh
```

### Advantages

✅ Fully automated - no manual device creation
✅ Complex hierarchies (sites, buildings, gateways)
✅ Correct device tokens automatically
✅ Reproducible setup
✅ Can provision hundreds of devices instantly

### When to Use

- You have access to the full repository
- You need complex asset/device hierarchies
- You want automated, repeatable setup
- You're testing gateway functionality
- You need many devices (100+)

---

## Workflow 2: Manual Setup (JAR Package Only)

**Best for**: Standalone JAR distribution without provisioning scripts

### What You Need
- Just the JAR package: `performance-tests-dist-4.0.1.zip`
- Java 17+
- ThingsBoard server access

### Setup Process

```bash
# 1. Extract package
unzip performance-tests-dist-4.0.1.zip
cd performance-tests-dist-4.0.1

# 2. Copy configuration template
cp .env.example .env

# 3. Edit .env with your settings
nano .env
```

### Configuration Example

```bash
# ThingsBoard Connection
REST_URL=http://your-server:8080
REST_USERNAME=tenant@thingsboard.org
REST_PASSWORD=tenant

# MQTT Settings
MQTT_HOST=your-server
MQTT_PORT=1883

# Test Configuration
TEST_PAYLOAD_TYPE=EBMPAPST_FFU
DEVICE_END_IDX=100
MESSAGES_PER_SECOND=50
DURATION_IN_SECONDS=300

# Device Management
DEVICE_CREATE_ON_START=true      # Auto-create devices
DEVICE_DELETE_ON_COMPLETE=false
```

### Running Tests

```bash
./run.sh

# Or directly:
source .env && java -jar tb-ce-performance-tests-4.0.1.jar
```

### What Happens

1. Application authenticates to ThingsBoard
2. If `DEVICE_CREATE_ON_START=true`:
   - Creates device profile
   - Creates devices (device_0, device_1, ..., device_99)
   - Assigns credentials
3. Connects devices via MQTT
4. Publishes telemetry
5. If `DEVICE_DELETE_ON_COMPLETE=true`:
   - Cleans up created devices

### Advantages

✅ Simple setup - just edit `.env`
✅ No Python/provisioning scripts needed
✅ Self-contained package
✅ Easy to distribute to teams
✅ No repository clone required

### Limitations

⚠️ No complex hierarchies (sites/buildings)
⚠️ No gateway provisioning
⚠️ Manual `.env` configuration
⚠️ No pre-created relationships

### When to Use

- You're distributing to users without repository access
- Simple device-only testing (no gateways)
- Quick performance validation
- Users don't have Python/provisioning tools
- Plug-and-play deployment needed

---

## Comparison Table

| Aspect | Workflow 1 (Provisioning) | Workflow 2 (Manual) |
|--------|--------------------------|---------------------|
| **Setup Time** | 2 min (automated) | 5 min (manual config) |
| **Device Creation** | Auto via script | Auto via app or manual |
| **Hierarchies** | ✅ Sites, buildings, gateways | ❌ Devices only |
| **Gateway Support** | ✅ Full gateway testing | ❌ Limited |
| **Reproducibility** | ✅ High (JSON scenarios) | ⚠️ Medium (manual .env) |
| **Distribution** | ❌ Needs full repo | ✅ Just ZIP package |
| **Complexity** | Medium (Python required) | Low (just Java) |
| **Best For** | Development, complex setups | Distribution, simple tests |

---

## Recommendation by Use Case

### Use Workflow 1 (Provisioning) When:

✅ You're the original developer/operator
✅ Testing complex scenarios with gateways
✅ Need reproducible multi-environment setup
✅ Setting up Hanoi Cleanroom scenario
✅ Have access to full repository
✅ Need 100+ devices with relationships

### Use Workflow 2 (Manual) When:

✅ Distributing to external teams/customers
✅ Simple performance validation
✅ Quick device-only tests
✅ Users don't have Python
✅ Plug-and-play deployment
✅ Testing < 100 devices

---

## Hybrid Approach

You can combine both workflows:

1. **Development**: Use provisioning for complex setup
2. **Distribution**: Package JAR with manual `.env` for end users
3. **Documentation**: Explain both options in README

---

## File Reference

### Provisioning Scripts (Workflow 1)
- `test-scenarios/provision-scenario.py` - Main provisioning script
- `test-scenarios/scenario-*.json` - Scenario definitions
- `test-scenarios/credentials.json` - ThingsBoard credentials
- `.env` - Auto-generated by provisioning

### Manual Setup (Workflow 2)
- `performance-tests-dist-4.0.1.zip` - Distribution package
- `.env.example` - Manual configuration template
- `run.sh` / `run.bat` - Launcher scripts
- `README.md` - Setup instructions

---

## Updated Package Release

The `package-release.sh` script now includes both workflows in the documentation:

1. **`.env.example`** - Explains both options at the top
2. **README.md** - Documents both workflows
3. **Run scripts** - Work with both workflows

This ensures users understand which workflow applies to them.

---

## Summary

**Answer to your question**: You're absolutely right to question this!

- **Provisioning workflow** (your main use case): `.env` is AUTO-GENERATED
- **Manual workflow** (JAR distribution): `.env` is MANUALLY CREATED from `.env.example`

The package now clarifies **both workflows** so users understand which one to use:
- If they have provisioning scripts → Use Option 1 (skip `.env.example`)
- If they only have the JAR → Use Option 2 (use `.env.example`)

This makes the package flexible for both scenarios! 🎯
