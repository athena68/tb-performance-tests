# Gateway Provisioning Guide

Comprehensive guide for gateway-based device provisioning in ThingsBoard.

---

## Table of Contents

1. [Overview](#overview)
2. [Gateway Setup](#gateway-setup)
3. [Auto-Provisioning Flow](#auto-provisioning-flow)
4. [Real-World Device Behavior](#real-world-device-behavior)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Gateway mode allows multiple devices to communicate through a single MQTT gateway connection. Devices are automatically provisioned when they connect via the gateway.

**Key Benefits:**
- Single gateway connection for many devices
- Automatic device provisioning
- Gateway-device relations automatically established
- Reduced connection overhead

---

## Gateway Setup

### Prerequisites

1. Gateway device must exist in ThingsBoard
2. Gateway must have access token configured
3. Gateway must be active and connected

### Configuration Steps

1. **Login to ThingsBoard UI**: http://your-server:8080

2. **Navigate to Gateway Device**:
   - Go to: Devices → Your Gateway → Manage credentials

3. **Set Access Token**:
   - Change the access token to match your configuration (e.g., `GW00000000`)
   - Save the gateway

4. **Verify Connection**:
   - Check gateway status shows "Active"
   - Check "Last Activity" timestamp is recent

---

## Auto-Provisioning Flow

### How It Works

When a device connects through the gateway, ThingsBoard automatically:
1. Creates the device if it doesn't exist
2. Sets the device type (if specified)
3. Establishes "Contains" relation from gateway to device
4. Activates the device

### Gateway Connect API

**Topic**: `v1/gateway/connect`

**Payload**:
```json
{
  "device": "DW00000000",
  "type": "EBMPAPST_FFU"
}
```

**Fields**:
- `device` (required): Device name
- `type` (optional): Device type (default: "default")

### Device Provisioning Sequence

```
Step 1: Gateway Connect
  └─> Topic: v1/gateway/connect
  └─> Payload: {"device":"DW00000000", "type":"EBMPAPST_FFU"}
  └─> Result: Device created + Gateway relation established

Step 2: Send Attributes (once - automatic)
  └─> Topic: v1/gateway/attributes
  └─> Payload: {"DW00000000": {"fanModel":"R3G355-AS03-01", ...}}

Step 3: Send Telemetry (continuous)
  └─> Topic: v1/gateway/telemetry
  └─> Payload: {"DW00000000": [{"ts":1234567890, "values":{...}}]}
```

### IMPORTANT: Device Creation Method

**✓ CORRECT** - Gateway Auto-Provisioning:
```bash
DEVICE_CREATE_ON_START=false  # Let gateway provision devices
```
- Devices created via `v1/gateway/connect`
- Gateway relations automatically established
- Device type properly set

**✗ INCORRECT** - REST API Creation:
```bash
DEVICE_CREATE_ON_START=true   # Creates via REST API
```
- Devices created without gateway relations
- Manual relation setup required
- Relations tab on gateway will be empty

---

## Real-World Device Behavior

### Actual IoT Device Lifecycle

Real IoT devices follow this pattern:

1. **Device Power-On / Boot**:
   - Connect to gateway/network
   - Send device attributes (bootstrap information)
   - Attributes include: firmware version, model, serial number, configuration

2. **Normal Operation**:
   - Send continuous telemetry
   - Update frequency: 1 Hz to 0.1 Hz depending on application
   - No attribute updates unless something changes

3. **Configuration Change**:
   - Only send attributes when firmware updates or config changes
   - Not on every cycle

4. **Device Reboot**:
   - Repeat step 1

### Implementation in Performance Tests

Our implementation mimics real-world behavior:

```java
// In MqttGatewayAPITest.java
@Override
public void sendInitialAttributes() throws InterruptedException {
    // Send attributes ONCE after device provisioning (bootstrap)
    log.info("Sending initial attributes for {} devices...", deviceClients.size());

    for (DeviceClient deviceClient : deviceClients) {
        byte[] payload = attrMsgGenerator.getNextMessage(
            deviceClient.getDeviceName(), false
        ).getData();

        deviceClient.getMqttClient().publish("v1/gateway/attributes",
            Unpooled.wrappedBuffer(payload),
            MqttQoS.AT_MOST_ONCE);
    }
}

// In GatewayBaseTestExecutor.java
@Override
protected void initEntities() throws Exception {
    if (testEnabled) {
        gatewayAPITest.connectGateways();
    }

    if (warmupEnabled) {
        gatewayAPITest.warmUpDevices();  // Provision devices
    }

    // Real-world behavior: Send attributes once after provisioning
    gatewayAPITest.sendInitialAttributes();

    // Then continuous telemetry (handled by test loop)
}
```

**Before (Manual Two-Step)**:
```bash
# Run 1: Send attributes
TEST_TELEMETRY=false ./start-ebmpapst-gateway.sh

# Run 2: Send telemetry
TEST_TELEMETRY=true ./start-ebmpapst-gateway.sh
```

**After (Automatic Real-World Behavior)**:
```bash
# Single run: provisions → attributes → telemetry
./start-ebmpapst-gateway.sh
```

---

## Configuration

### `.env.ebmpapst-gateway` File

```bash
# ThingsBoard Server
REST_URL=http://your-thingsboard-server.com:8080
REST_USERNAME=your-username@domain.com
REST_PASSWORD=your-password

# MQTT Broker
MQTT_HOST=your-mqtt-broker.com
MQTT_PORT=1883

# *** CRITICAL: Use GATEWAY mode ***
TEST_API=gateway
DEVICE_API=MQTT

# Gateway Configuration
GATEWAY_START_IDX=0
GATEWAY_END_IDX=1              # Using 1 gateway only
GATEWAY_CREATE_ON_START=false  # ← DO NOT create (already exists)
GATEWAY_DELETE_ON_COMPLETE=false

# Device Configuration
DEVICE_START_IDX=0
DEVICE_END_IDX=60              # 60 FFU devices
DEVICE_CREATE_ON_START=false   # ← IMPORTANT: Let gateway auto-provision!
DEVICE_DELETE_ON_COMPLETE=false

# CRITICAL: In gateway mode, devices MUST be created by gateway connect API
# If DEVICE_CREATE_ON_START=true, devices are created via REST without gateway relations
# Setting it to false allows gateway to auto-provision and establish relations

# Test Execution
WARMUP_ENABLED=true
TEST_ENABLED=true
MESSAGES_PER_SECOND=60
DURATION_IN_SECONDS=86400  # 24 hours

# Test Payload Type
TEST_PAYLOAD_TYPE=EBMPAPST_FFU
```

---

## Troubleshooting

### Problem: Gateway Relations Tab is Empty

**Symptoms**:
- Devices exist in ThingsBoard
- Gateway shows no relations to devices
- Devices can't be seen from gateway perspective

**Cause**: Devices were created via REST API (`DEVICE_CREATE_ON_START=true`)

**Solution**:
1. Set `DEVICE_CREATE_ON_START=false`
2. Delete existing devices
3. Restart test to let gateway auto-provision

**Verification**:
```bash
# Check gateway relations
curl -X GET "http://your-server:8080/api/relations?fromId=<GATEWAY_ID>&fromType=DEVICE" \
  -H "X-Authorization: Bearer <TOKEN>"

# Should return array with 60 device relations
```

---

### Problem: Devices Have Type "default" Instead of "EBMPAPST_FFU"

**Symptoms**:
- Devices created but with wrong type
- Dashboard entity filter not matching devices

**Cause**: Gateway connect payload missing device type

**Solution**:
Update `MqttGatewayAPITest.java`:
```java
protected byte[] getData(String deviceName) {
    // Include device type in gateway connect
    return ("{\"device\":\"" + deviceName + "\",\"type\":\"EBMPAPST_FFU\"}")
        .getBytes(StandardCharsets.UTF_8);
}
```

Then rebuild:
```bash
mvn clean package -DskipTests
```

---

### Problem: Attributes Not Showing

**Symptoms**:
- Telemetry data visible
- No attributes on devices

**Cause**: Attributes not sent after provisioning

**Solution**: Already fixed in current implementation. The `sendInitialAttributes()` method is automatically called after device provisioning.

**Manual Test**:
```bash
# Send attributes to single device via gateway
mosquitto_pub -h 167.99.64.71 -p 1883 \
  -u "GW00000000" \
  -t "v1/gateway/attributes" \
  -m '{"DW00000000": {"fanModel":"R3G355-AS03-01"}}'
```

---

## Files Modified

1. **src/main/java/org/thingsboard/tools/service/gateway/MqttGatewayAPITest.java**
   - Added `sendInitialAttributes()` method
   - Modified `getData()` to include device type

2. **src/main/java/org/thingsboard/tools/service/GatewayBaseTestExecutor.java**
   - Added automatic attribute sending after warmup

3. **.env.ebmpapst-gateway**
   - Set `DEVICE_CREATE_ON_START=false`
   - Set `GATEWAY_CREATE_ON_START=false`

---

## Quick Start

```bash
# 1. Verify setup
./verify-current-setup.sh

# 2. Run performance test (provisions + attributes + telemetry)
./start-ebmpapst-gateway.sh

# 3. Check results
# - ThingsBoard UI: http://167.99.64.71:8080
# - Navigate to: Devices → DW00000000
# - Check: Latest telemetry, Attributes, Relations tabs
```

---

## References

- [ThingsBoard Gateway MQTT API](https://thingsboard.io/docs/reference/gateway-mqtt-api/)
- [Device Provisioning](https://thingsboard.io/docs/user-guide/device-provisioning/)
- [Gateway Relations](https://thingsboard.io/docs/user-guide/entities-and-relations/)

---

**Last Updated**: 2025-10-17
