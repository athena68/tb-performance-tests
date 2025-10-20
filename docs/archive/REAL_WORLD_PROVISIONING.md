# Real-World Device Provisioning Implementation

## Summary

The performance test framework has been enhanced to automatically mimic real-world IoT device behavior during gateway provisioning.

---

## What Changed?

### Before (Manual Two-Step Process):

1. Run test with `TEST_TELEMETRY=false` to send attributes
2. Run test again with `TEST_TELEMETRY=true` to send telemetry

**Problem:** This doesn't match how real devices behave!

### After (Automatic Real-World Behavior):

1. Run test **ONCE**: `./start-ebmpapst-gateway.sh`
2. Test automatically:
   - Provisions devices via `v1/gateway/connect`
   - Sends attributes **ONCE** (bootstrap)
   - Sends continuous telemetry

**Result:** Mimics actual device lifecycle!

---

## Real-World Device Lifecycle

### Physical Device Behavior:

```
1. Device Power-On / Boot
   ├─> Connect to gateway
   ├─> Send attributes (firmware version, model, serial number, config)
   └─> Start sending telemetry (temperature, speed, pressure, etc.)

2. Normal Operation
   └─> Continuous telemetry updates (every second/minute)

3. Attribute Changes (Rare)
   └─> Send updated attribute when firmware upgrades or config changes

4. Device Reboot
   └─> Repeat step 1 (send attributes again, then telemetry)
```

### What This Means for ThingsBoard:

- **Attributes** = Semi-static device metadata (sent once at startup)
  - Examples: `fanModel`, `manufacturer`, `firmwareVersion`, `serialNumber`
  - Frequency: Once per boot, or when changed

- **Telemetry** = Real-time sensor data (sent continuously)
  - Examples: `actualSpeed`, `temperature`, `pressure`, `powerConsumption`
  - Frequency: Every 1-60 seconds

---

## Implementation Details

### Code Changes:

#### 1. Added `sendInitialAttributes()` Method

**File:** `MqttGatewayAPITest.java`

```java
@Override
public void sendInitialAttributes() throws InterruptedException {
    log.info("Sending initial attributes for {} devices...", deviceClients.size());

    for (DeviceClient deviceClient : deviceClients) {
        // Get attribute message from attribute generator
        byte[] payload = attrMsgGenerator.getNextMessage(deviceClient.getDeviceName(), false).getData();

        // Publish to v1/gateway/attributes
        deviceClient.getMqttClient().publish("v1/gateway/attributes", ...);
    }
}
```

#### 2. Updated Test Execution Flow

**File:** `GatewayBaseTestExecutor.java`

```java
protected void initEntities() throws Exception {
    // Step 1: Connect gateway MQTT clients
    gatewayAPITest.connectGateways();

    // Step 2: Provision devices (v1/gateway/connect)
    if (warmupEnabled) {
        gatewayAPITest.warmUpDevices();
    }

    // Step 3: Send attributes once (NEW!)
    gatewayAPITest.sendInitialAttributes();
}

protected void runApiTests() throws InterruptedException {
    // Step 4: Send continuous telemetry
    gatewayAPITest.runApiTests();
}
```

#### 3. Hardcoded Telemetry for Test Phase

**File:** `MqttGatewayAPITest.java`

```java
@Override
protected String getTestTopic() {
    // Gateway mode: attributes sent once during initialization
    // Test phase ALWAYS sends continuous telemetry
    return "v1/gateway/telemetry";
}

@Override
protected Msg getNextMessage(String deviceName, boolean alarmRequired) {
    // Always use telemetry generator for test phase
    return tsMsgGenerator.getNextMessage(deviceName, alarmRequired);
}
```

---

## Message Flow Diagram

```
Gateway Test Execution
│
├─ Phase 1: Gateway Connection
│  └─> Gateway MQTT client connects with token GW00000000
│
├─ Phase 2: Device Provisioning (Warmup)
│  ├─> Topic: v1/gateway/connect
│  ├─> Payload: {"device":"DW00000000", "type":"EBMPAPST_FFU"}
│  ├─> Payload: {"device":"DW00000001", "type":"EBMPAPST_FFU"}
│  └─> Result: 50 devices created with gateway relations
│
├─ Phase 3: Initial Attributes (NEW - Automatic)
│  ├─> Topic: v1/gateway/attributes
│  ├─> Payload: {
│  │     "DW00000000": {
│  │       "fanModel": "R3G355-AS03-01",
│  │       "manufacturer": "ebm-papst",
│  │       "firmwareVersion": "ACE-4.3",
│  │       ...
│  │   
│  │     "DW00000001": { ... },
│  │     ...
│  │   }
│  └─> Result: All devices have attributes populated
│
└─ Phase 4: Continuous Telemetry (Test Phase)
   ├─> Topic: v1/gateway/telemetry
   ├─> Payload (every second): {
   │     "DW00000000": [{
   │       "ts": 1234567890000,
   │       "values": {
   │         "actualSpeed": 1547,
   │         "dcLinkVoltage": 398.5,
   │         "powerConsumption": 1315,
   │         ...
   │       }
   │     }],
   │     "DW00000001": [ ... ],
   │     ...
   │   }
   └─> Result: Continuous telemetry for 300+ seconds
```

---

## Configuration

### Updated `.env.ebmpapst-gateway`:

```bash
# Test Execution Configuration
WARMUP_ENABLED=true
TEST_ENABLED=true
# NOTE: TEST_TELEMETRY is ignored in gateway mode
# Real-world device behavior: Attributes sent ONCE after provisioning, then continuous telemetry

# Message Rate Configuration
MESSAGES_PER_SECOND=50         # 50 devices × 1 msg/sec
DURATION_IN_SECONDS=300        # 5 minutes of continuous telemetry
```

---

## Usage

### Single Command - No Manual Steps!

```bash
# Clean up old test data (optional)
./cleanup-test-devices.sh

# Run gateway test - fully automatic!
./start-ebmpapst-gateway.sh
```

### What Happens:

1. Gateway connects (GW00000000)
2. 50 devices provisioned (DW00000000 - DW00000049)
3. Attributes sent automatically for all 50 devices
4. Telemetry streams continuously for 5 minutes (50 msg/sec)
5. Test completes

### Verification on ThingsBoard UI:

1. **Relations:** Gateway GW00000000 → Relations tab → See 50 devices
2. **Attributes:** Device DW00000000 → Attributes tab → Client scope → See fanModel, manufacturer, etc.
3. **Telemetry:** Device DW00000000 → Latest telemetry → See actualSpeed, temperature, etc.

---

## Benefits

### ✅ Matches Real-World Behavior:
- Devices send attributes once at startup (bootstrap)
- Then continuous telemetry
- On reboot, repeat the cycle

### ✅ Single Command Execution:
- No manual TEST_TELEMETRY flag switching
- No separate attribute/telemetry runs
- One command handles everything

### ✅ Accurate Performance Testing:
- Tests the actual device provisioning flow
- Measures realistic attribute + telemetry workload
- Gateway handles mixed message types (connect, attributes, telemetry)

### ✅ Better User Experience:
- Simpler to use
- Less error-prone
- Matches IoT best practices

---

## Technical Notes

### For Device Mode (Non-Gateway):

Device mode (direct MQTT connection) still supports `TEST_TELEMETRY` flag for flexibility:
- `TEST_TELEMETRY=true` → continuous telemetry
- `TEST_TELEMETRY=false` → continuous attributes (for testing only)

### For Gateway Mode:

Gateway mode **always** follows real-world lifecycle:
1. Connect devices
2. Send attributes once
3. Send continuous telemetry

The `TEST_TELEMETRY` configuration is **ignored** in gateway mode.

---

## Troubleshooting

### Attributes Not Showing?

**Check logs for:**
```
Sending initial attributes for 50 devices...
Initial attributes sent successfully for 50 devices! Failed: 0
```

If you see failures, check:
- Gateway token is correct (GW00000000)
- Gateway is connected
- WARMUP_ENABLED=true (devices must be provisioned first)

### Relations Still Empty?

Ensure:
- `DEVICE_CREATE_ON_START=false` (let gateway auto-provision)
- `WARMUP_ENABLED=true` (sends v1/gateway/connect)
- Check logs for "Warming up 50 devices..."

---

## References

- [ThingsBoard Gateway MQTT API](https://thingsboard.io/docs/reference/gateway-mqtt-api/)
- [ThingsBoard Attributes](https://thingsboard.io/docs/user-guide/attributes/)
- [Device Provisioning Guide](./PROVISIONING_GUIDE.md)
- [ebmpapst FFU Specifications](./FFU_TEST_EBMPAPST.md)
