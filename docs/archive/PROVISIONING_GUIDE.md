# ThingsBoard Device Provisioning & Data Flow Guide

This guide explains the correct order for device provisioning, attributes, and telemetry in ThingsBoard, specifically for gateway-based deployments.

---

## Understanding ThingsBoard Device Provisioning

### What is Provisioning?

**Provisioning** is the process of registering a device in ThingsBoard so it can send data and receive commands. There are multiple provisioning strategies:

1. **Manual Provisioning** (via UI/REST API)
2. **Auto-Provisioning** (via Gateway Connect API)
3. **Device Provisioning Protocol** (advanced, certificate-based)

---

## Gateway Mode: Auto-Provisioning Flow

### ✅ Correct Flow (Gateway Mode with Auto-Provisioning):

```
Step 1: Gateway Connect
  └─> Topic: v1/gateway/connect
  └─> Payload: {"device":"DW00000000", "type":"EBMPAPST_FFU"}
  └─> Result: Device created + Gateway relation established

Step 2: Send Attributes (once)
  └─> Topic: v1/gateway/attributes
  └─> Payload: {"DW00000000": {"fanModel":"R3G355-AS03-01", ...}}
  └─> Result: Device attributes populated

Step 3: Send Telemetry (continuous)
  └─> Topic: v1/gateway/telemetry
  └─> Payload: {"DW00000000": [{"ts":1234567890, "values":{...}}]}
  └─> Result: Device telemetry updated
```

### How Auto-Provisioning Works:

When gateway publishes to `v1/gateway/connect`:

1. **ThingsBoard checks**: Does device "DW00000000" exist?

2. **If NO** → ThingsBoard automatically:
   - Creates new device with name "DW00000000"
   - Assigns device profile type "EBMPAPST_FFU" (if specified)
   - Creates "Contains" relation: Gateway → Device
   - Generates device credentials
   - **Device is now provisioned!**

3. **If YES** → ThingsBoard:
   - Skips device creation
   - Updates "last activity" timestamp
   - Does NOT create duplicate relations

---

## ❌ Common Mistake: Pre-Creating Devices

### What Happens When `DEVICE_CREATE_ON_START=true` in Gateway Mode:

```
Step 1: REST API creates device
  └─> POST /api/device
  └─> Device exists WITHOUT gateway relation

Step 2: Gateway tries to connect
  └─> Topic: v1/gateway/connect
  └─> ThingsBoard: "Device already exists, skip creation"
  └─> NO RELATION CREATED!

Result: Device exists but NOT under gateway in Relations tab
```

### The Fix:

**In gateway mode, always use `DEVICE_CREATE_ON_START=false`** to allow gateway API to create devices with proper relations.

---

## Configuration Comparison

### Direct Device Mode (No Gateway):

```.env
TEST_API=device
DEVICE_CREATE_ON_START=true    # ✅ Create via REST API
DEVICE_API=MQTT

# Device connects directly to ThingsBoard
# Topic: v1/devices/me/telemetry
```

### Gateway Mode (With Gateway):

```.env
TEST_API=gateway
GATEWAY_CREATE_ON_START=false  # Use existing gateway
DEVICE_CREATE_ON_START=false   # ✅ Let gateway auto-provision!
DEVICE_API=MQTT

# Gateway connects devices via gateway API
# Topic: v1/gateway/connect, v1/gateway/telemetry
```

---

## Detailed Message Flow Example

### Example: Provisioning 3 FFU Devices via Gateway

**1. Gateway Connects to ThingsBoard:**

```bash
# Gateway (token: GW00000000) connects
Topic: N/A (gateway already connected)
```

**2. Connect Child Devices:**

```bash
Topic: v1/gateway/connect
Payload:
{
  "device": "DW00000000",
  "type": "EBMPAPST_FFU"
}
```

Repeat for DW00000001, DW00000002...

**Result:** 3 devices created with:
- Device Profile: EBMPAPST_FFU
- Relations: Gateway "Contains" each device

**3. Send Attributes (Static Metadata):**

```bash
Topic: v1/gateway/attributes
Payload:
{
  "DW00000000": {
    "fanModel": "R3G355-AS03-01",
    "manufacturer": "ebm-papst",
    "firmwareVersion": "ACE-4.3",
    "serialNumber": "EBM-0547-234567",
    "modbusAddress": 15,
    "ratedSpeed": 1800,
    "ratedPower": 1500

  "DW00000001": { ... },
  "DW00000002": { ... }
}
```

**Result:** Each device has attributes populated.

**4. Send Telemetry (Real-time Data):**

```bash
Topic: v1/gateway/telemetry
Payload:
{
  "DW00000000": [{
    "ts": 1234567890000,
    "values": {
      "actualSpeed": 1547,
      "dcLinkVoltage": 398.5,
      "dcLinkCurrent": 3.67,
      "powerConsumption": 1315,
      "differentialPressure": 287,
      "motorTemperature": 52,
      "operatingStatus": "RUNNING"
    }
  }],
  "DW00000001": [{ ... }],
  "DW00000002": [{ ... }]
}
```

**Result:** Each device shows latest telemetry values.

---

## Provisioning Strategies Comparison

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| **REST API Pre-Creation** | Direct device mode | Full control, custom attributes | No gateway relations, more API calls |
| **Gateway Auto-Provision** | Gateway mode | Automatic, relations created | Less control over device config |
| **Device Provisioning Protocol** | Production, certificate-based | Secure, credential rotation | Complex setup |

---

## Correct Test Configuration

### For Gateway Mode (Your Setup):

```bash
# .env.ebmpapst-gateway

# Gateway settings
TEST_API=gateway
GATEWAY_CREATE_ON_START=false      # Your gateway already exists
GATEWAY_START_IDX=0
GATEWAY_END_IDX=1

# Device settings
DEVICE_CREATE_ON_START=false       # ✅ CRITICAL: Let gateway auto-provision!
DEVICE_START_IDX=0
DEVICE_END_IDX=50

# Test settings
TEST_PAYLOAD_TYPE=EBMPAPST_FFU
WARMUP_ENABLED=true                # This sends v1/gateway/connect
```

### Execution Flow (Automatic Real-World Behavior):

The test now automatically mimics real-world device provisioning:

1. **Warmup Phase** (`WARMUP_ENABLED=true`):
   - Publishes to `v1/gateway/connect` for each device
   - Devices are auto-provisioned with gateway relations

2. **Initial Attributes Phase** (Automatic):
   - Publishes to `v1/gateway/attributes` **ONCE** for each device
   - Mimics device bootstrap behavior
   - Attributes populated automatically (no manual step needed)

3. **Telemetry Phase** (Continuous):
   - Publishes to `v1/gateway/telemetry` continuously
   - Real-time data stream for the test duration

### One-Command Execution:

```bash
# Single command - handles everything automatically!
./start-ebmpapst-gateway.sh
```

This mimics real device behavior:
- Device powers on → sends attributes once (bootstrap)
- Then sends continuous telemetry
- On reboot → repeats the same cycle

---

## Why Attributes First, Then Telemetry?

### Recommended Order:

```
1. Connect → Device provisioned
2. Attributes → Static metadata populated
3. Telemetry → Real-time data streaming
```

### Reasoning:

**Attributes** (sent once):
- Static device metadata (model, serial, configuration)
- Used for device identification and filtering
- Displayed in device details
- Example: fanModel, manufacturer, serialNumber

**Telemetry** (sent continuously):
- Real-time sensor data
- Time-series values
- Used for monitoring and visualization
- Example: temperature, speed, pressure

**If you send telemetry first:**
- ✅ Works fine - data is received
- ❌ Device appears with no context (no model, no serial)
- ❌ Users see telemetry but don't know device details

**If you send attributes first:**
- ✅ Device is properly identified
- ✅ Attributes provide context for telemetry
- ✅ Better UX for operators

---

## Testing the Correct Flow

### Step 1: Delete Existing Devices (if any)

```bash
./cleanup-test-devices.sh
# Choose option: Delete devices by name range
```

### Step 2: Run Gateway Test with Auto-Provisioning

```bash
# Make sure settings are correct
cat .env.ebmpapst-gateway | grep -E "DEVICE_CREATE_ON_START|TEST_API|WARMUP_ENABLED"

# Expected output:
# TEST_API=gateway
# GATEWAY_CREATE_ON_START=false
# DEVICE_CREATE_ON_START=false    # ← MUST be false!
# WARMUP_ENABLED=true              # ← Triggers v1/gateway/connect

# Run test
./start-ebmpapst-gateway.sh
```

### Step 3: Verify Gateway Relations

On ThingsBoard UI:

```
1. Go to: Devices → Your Gateway (GW00000000)
2. Click "Relations" tab
3. ✅ You should now see 50 FFU devices listed!
4. Each device shows:
   - Type: Device
   - Direction: To (outbound from gateway)
   - Relation type: Contains
```

### Step 4: Populate Attributes

```bash
# Set telemetry to false for attributes
export TEST_TELEMETRY=false
export DEVICE_CREATE_ON_START=false  # Devices already exist
export DURATION_IN_SECONDS=10        # Quick run

./start-ebmpapst-gateway.sh
```

### Step 5: Verify Complete Setup

```
1. Gateway → Relations tab: ✅ 50 devices
2. Device DW00000000 → Attributes: ✅ fanModel, manufacturer, etc.
3. Device DW00000000 → Latest telemetry: ✅ actualSpeed, temperature, etc.
```

---

## Troubleshooting

### Issue: "Relations tab still empty"

**Check:**
```bash
# 1. Verify DEVICE_CREATE_ON_START=false
grep DEVICE_CREATE_ON_START .env.ebmpapst-gateway

# 2. Check test logs for "v1/gateway/connect"
# Should see: "Warming up 50 devices..."
# Should see: "Message published to v1/gateway/connect"

# 3. Delete devices and re-run
./cleanup-test-devices.sh
./start-ebmpapst-gateway.sh
```

### Issue: "Devices have telemetry but no attributes"

**Solution:**
```bash
# Run attributes population
export TEST_TELEMETRY=false
export DEVICE_CREATE_ON_START=false
export DURATION_IN_SECONDS=10
./start-ebmpapst-gateway.sh
```

### Issue: "Gateway not found"

**Solution:**
```bash
# Ensure gateway token is exactly: GW00000000
# ThingsBoard UI → Gateway → Manage credentials → Access token
# Must be: GW00000000 (10 characters, GW + 8 zeros)
```

---

## Performance Considerations

### Attribute vs Telemetry Volume:

| Data Type | Frequency | Volume | Storage |
|-----------|-----------|--------|---------|
| **Attributes** | Once per device | Low | Persistent |
| **Telemetry** | Every second | High | Time-series |

**Best Practice:**
- Send attributes once at device startup
- Send telemetry continuously during operation
- Update attributes only when device config changes

### Batch Size Recommendations:

```bash
# For 50 devices through 1 gateway:
MESSAGES_PER_SECOND=50       # 1 msg/sec per device
WARMUP_PACK_SIZE=100         # Connect 100 devices at once

# For 500 devices through 1 gateway:
MESSAGES_PER_SECOND=100      # Lower rate
WARMUP_PACK_SIZE=100         # Smaller batches

# For 5000 devices through 10 gateways:
GATEWAY_END_IDX=10           # 10 gateways
MESSAGES_PER_SECOND=1000     # Distributed load
```

---

## Summary: The Golden Rules

### ✅ DO:

1. **Gateway Mode**: Set `DEVICE_CREATE_ON_START=false`
2. **Let gateway auto-provision** devices via `v1/gateway/connect`
3. **Send attributes first** (once per device)
4. **Send telemetry continuously** for monitoring
5. **Enable warmup** (`WARMUP_ENABLED=true`) to trigger connect

### ❌ DON'T:

1. **Don't pre-create devices via REST** in gateway mode
2. **Don't skip warmup** - it establishes device connections
3. **Don't send telemetry without attributes** - context is important
4. **Don't create duplicate devices** - check existing first

---

## Quick Reference: Test Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `start-ebmpapst-ffu.sh` | Direct device test | No gateway, direct MQTT |
| `start-ebmpapst-gateway.sh` | Gateway mode test | With existing gateway |
| `populate-ebmpapst-attributes.sh` | Populate attributes | After telemetry test |
| `cleanup-test-devices.sh` | Delete test devices | Before new test run |

---

## Further Reading

- [ThingsBoard Gateway MQTT API](https://thingsboard.io/docs/reference/gateway-mqtt-api/)
- [ThingsBoard Device Provisioning](https://thingsboard.io/docs/user-guide/device-provisioning/)
- [ThingsBoard Entities and Relations](https://thingsboard.io/docs/user-guide/entities-and-relations/)

---

**Next Steps:**
1. ✅ Fix gateway configuration (`.env.ebmpapst-gateway`)
2. ✅ Run cleanup script to remove old devices
3. ✅ Run gateway test with auto-provisioning
4. ✅ Verify relations in ThingsBoard UI
5. ✅ Populate attributes
6. ✅ Enjoy proper ebmpapst FFU monitoring! 🎉
