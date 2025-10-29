# Gateway Device Relation Guide

**Research Investigation**: How to create devices from gateway with proper "Created" relations

**Date**: 2025-10-29
**Scenario**: Hanoi Cleanroom Facility
**Configuration**: `.env.ebmpapst-gateway` + `test-scenarios/scenario-hanoi-cleanroom.json`

---

## Executive Summary

This document provides comprehensive guidance on creating devices through ThingsBoard gateways so that proper bidirectional "Created" relations are automatically established between gateways and their child devices.

### Key Findings

✅ **Automatic Relation Creation**: ThingsBoard automatically creates "Contains" relations (not "Created") when devices are provisioned via Gateway MQTT API
✅ **Gateway MQTT API**: The `v1/gateway/connect` topic is the correct method for device provisioning
✅ **No Manual Relation Creation Needed**: Relations are established automatically by ThingsBoard when using gateway provisioning
❌ **REST API Creation**: Creating devices via REST API does NOT establish gateway relations

---

## Understanding ThingsBoard Gateway Relations

### Relation Types

ThingsBoard uses **"Contains"** relation type (not "Created") for gateway-device relationships:

```
Gateway --[Contains]--> Device   (Outbound relation from gateway)
Device --[Contains]--> Gateway   (Inbound relation to gateway, appears as outbound "To" from device perspective)
```

**Note**: The ThingsBoard documentation and API primarily use "Contains" for gateway-device relationships, though the UI may display this differently depending on the view direction.

---

## Gateway MQTT API Device Provisioning

### 1. Device Connect Message

**Topic**: `v1/gateway/connect`

**Payload Structure**:
```json
{
  "device": "DW00000000",
  "type": "EBMPAPST_FFU"
}
```

**Fields**:
- `device` (required): Device name (e.g., "DW00000000", "DW00000001")
- `type` (optional): Device profile type (defaults to "default" if omitted)

### 2. How ThingsBoard Processes Gateway Connect

When ThingsBoard receives a `v1/gateway/connect` message:

1. **Device Lookup/Creation**:
   - Searches for existing device by name
   - Creates new device if it doesn't exist
   - Sets device profile based on `type` field

2. **Automatic Relation Establishment**:
   - Creates **"Contains"** relation from Gateway to Device
   - Sets relation direction: `FROM` gateway `TO` device
   - Relation type: `Contains`

3. **Device Activation**:
   - Marks device as active
   - Associates device with the gateway's tenant
   - Enables attribute updates and RPC commands through gateway

### 3. Complete Device Provisioning Sequence

```
Step 1: Gateway Authentication
  └─> Gateway connects to MQTT broker using access token
  └─> Topic: N/A (standard MQTT CONNECT)
  └─> Credentials: username = gateway_access_token, password = (empty)

Step 2: Device Provisioning (via Gateway)
  └─> Topic: v1/gateway/connect
  └─> Payload: {"device":"DW00000000", "type":"EBMPAPST_FFU"}
  └─> Result: Device created + "Contains" relation established
  └─> Relation: Gateway --[Contains]--> DW00000000

Step 3: Send Initial Attributes (Bootstrap)
  └─> Topic: v1/gateway/attributes
  └─> Payload: {"DW00000000": {"fanModel":"R3G355-AS03-01", "firmwareVersion":"2.1.5", ...}}
  └─> Result: Device attributes populated (one-time)

Step 4: Continuous Telemetry
  └─> Topic: v1/gateway/telemetry
  └─> Payload: {"DW00000000": [{"ts":1234567890000, "values":{"temperature":25.5, ...}}]}
  └─> Result: Time-series data ingestion (continuous)
```

---

## Implementation in Performance Tests

### Current Implementation (Correct)

Our current implementation in `MqttGatewayAPITest.java` correctly uses the Gateway MQTT API:

#### File: `src/main/java/org/thingsboard/tools/service/gateway/MqttGatewayAPITest.java`

**Key Methods**:

1. **Device Connect (Provisioning)** - Line 267-275:
```java
@Override
protected String getWarmUpTopic() {
    return "v1/gateway/connect";
}

@Override
protected byte[] getData(String deviceName) {
    // Include device type in gateway connect to ensure proper device provisioning
    return ("{\"device\":\"" + deviceName + "\",\"type\":\"EBMPAPST_FFU\"}").getBytes(StandardCharsets.UTF_8);
}
```

2. **Initial Attributes** - Line 218-258:
```java
@Override
public void sendInitialAttributes() throws InterruptedException {
    log.info("Sending initial attributes for {} devices...", deviceClients.size());
    AtomicInteger totalSent = new AtomicInteger();
    AtomicInteger totalFailed = new AtomicInteger();
    CountDownLatch latch = new CountDownLatch(deviceClients.size());

    for (DeviceClient deviceClient : deviceClients) {
        restClientService.getScheduler().submit(() -> {
            try {
                // Get attribute message from attribute generator
                byte[] payload = attrMsgGenerator.getNextMessage(deviceClient.getDeviceName(), false).getData();

                deviceClient.getMqttClient().publish("v1/gateway/attributes",
                    io.netty.buffer.Unpooled.wrappedBuffer(payload),
                    io.netty.handler.codec.mqtt.MqttQoS.AT_MOST_ONCE)
                        .addListener(future -> {
                            if (future.isSuccess()) {
                                totalSent.incrementAndGet();
                            } else {
                                totalFailed.incrementAndGet();
                                log.error("Failed to send initial attributes for device: {}",
                                    deviceClient.getDeviceName(), future.cause());
                            }
                            latch.countDown();
                        });
            } catch (Exception e) {
                totalFailed.incrementAndGet();
                log.error("Error preparing attributes for device: {}", deviceClient.getDeviceName(), e);
                latch.countDown();
            }
        });
    }

    boolean completed = latch.await(60, TimeUnit.SECONDS);
    if (completed) {
        log.info("Initial attributes sent successfully for {} devices! Failed: {}",
            totalSent.get(), totalFailed.get());
    } else {
        log.error("Timeout while sending initial attributes! Sent: {}, Failed: {}, Remaining: {}",
            totalSent.get(), totalFailed.get(), latch.getCount());
    }
}
```

3. **Continuous Telemetry** - Line 283-294:
```java
@Override
protected String getTestTopic() {
    // Gateway mode: attributes are sent once during initialization
    // Test phase always sends continuous telemetry
    return "v1/gateway/telemetry";
}

@Override
protected org.thingsboard.tools.service.msg.Msg getNextMessage(String deviceName, boolean alarmRequired) {
    // Gateway mode: always use telemetry generator for test phase
    // Attributes are sent separately during initialization
    return tsMsgGenerator.getNextMessage(deviceName, alarmRequired);
}
```

### Configuration Requirements

#### `.env.ebmpapst-gateway` Configuration

**Critical Settings**:
```bash
# Gateway Mode
TEST_API=gateway                 # Use gateway API (not device API)
DEVICE_API=MQTT                  # Gateway uses MQTT protocol

# Gateway Configuration
GATEWAY_START_IDX=0
GATEWAY_END_IDX=2                # 2 gateways (GW00000000, GW00000001)
GATEWAY_CREATE_ON_START=false    # Gateways already created by provisioner

# Device Configuration
DEVICE_START_IDX=0
DEVICE_END_IDX=60                # 60 devices (DW00000000 - DW00000059)
DEVICE_CREATE_ON_START=false     # ⚠️ CRITICAL: Must be false!

# Why DEVICE_CREATE_ON_START must be false:
# - When true: Devices created via REST API without gateway relations
# - When false: Devices auto-provisioned via v1/gateway/connect with relations
```

---

## Verifying Relations

### REST API to Check Gateway Relations

After devices are provisioned via gateway, verify relations using REST API:

**Endpoint**: `GET /api/relations`

**Query Parameters**:
- `fromId`: Gateway device ID (UUID)
- `fromType`: "DEVICE"

**Example**:
```bash
# Get gateway ID first
GATEWAY_ID=$(curl -s -X GET "https://demo.thingsboard.io/api/tenant/devices?deviceName=GW00000000" \
  -H "X-Authorization: Bearer $TOKEN" | jq -r '.id.id')

# Get gateway relations
curl -s -X GET "https://demo.thingsboard.io/api/relations?fromId=$GATEWAY_ID&fromType=DEVICE" \
  -H "X-Authorization: Bearer $TOKEN" | jq .
```

**Expected Response**:
```json
[
  {
    "from": {
      "entityType": "DEVICE",
      "id": "gateway-uuid-here"
  
    "to": {
      "entityType": "DEVICE",
      "id": "device-uuid-here"
  
    "type": "Contains",
    "typeGroup": "COMMON"

  ...
]
```

### UI Verification

1. **Navigate to Gateway Device**:
   - Login to ThingsBoard UI
   - Go to: Devices → GW00000000

2. **Check Relations Tab**:
   - Click on "Relations" tab
   - Should see list of devices with relation type "Contains"
   - Direction: Outbound (From gateway)

3. **Check Device Relations** (from device perspective):
   - Go to: Devices → DW00000000
   - Click on "Relations" tab
   - Should see gateway with relation type "Contains"
   - Direction: Inbound (To device, but may display as outbound "To" gateway)

---

## Scenario Configuration

### Hanoi Cleanroom Facility Setup

**File**: `test-scenarios/scenario-hanoi-cleanroom.json`

```json
{
  "scenarioName": "Hanoi Cleanroom Facility",
  "buildings": [
    {
      "name": "FPT Building Duy Tan",
      "floors": [
        {
          "name": "Floor 5",
          "rooms": [
            {
              "name": "Room R501",
              "gateways": [
                {
                  "name": "GW00000000",
                  "devices": {
                    "prefix": "DW",
                    "start": 0,
                    "end": 29,
                    "count": 30
                  }
                }
              ]
          
            {
              "name": "Room R502",
              "gateways": [
                {
                  "name": "GW00000001",
                  "devices": {
                    "prefix": "DW",
                    "start": 30,
                    "end": 59,
                    "count": 30
                  }
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "totals": {
    "gateways": 2,
    "devices": 60
  }
}
```

**Gateway-Device Mapping**:
- GW00000000 → DW00000000 to DW00000029 (30 devices)
- GW00000001 → DW00000030 to DW00000059 (30 devices)

---

## Common Issues and Solutions

### Issue 1: Gateway Relations Tab Empty

**Symptoms**:
- Devices exist in ThingsBoard
- Gateway shows no relations to devices
- Devices appear disconnected from gateway

**Cause**:
- `DEVICE_CREATE_ON_START=true` (devices created via REST API)

**Solution**:
```bash
# 1. Update configuration
DEVICE_CREATE_ON_START=false

# 2. Delete existing devices
# (Use ThingsBoard UI or REST API)

# 3. Restart test to trigger auto-provisioning
./start-ebmpapst-gateway.sh
```

### Issue 2: Wrong Relation Type ("Created" vs "Contains")

**Symptoms**:
- Expected "Created" relations
- Actually see "Contains" relations

**Clarification**:
- ThingsBoard uses **"Contains"** for gateway-device relationships
- This is the correct and expected relation type
- "Created" may be a custom relation type for specific use cases

**Action**:
- No action needed - "Contains" is correct
- If "Created" is required, manual relation creation via REST API is needed (not automatic)

### Issue 3: Devices Have Wrong Type

**Symptoms**:
- Devices created with type "default" instead of "EBMPAPST_FFU"
- Dashboard filters don't match devices

**Cause**:
- Missing `type` field in `v1/gateway/connect` payload

**Solution**:
Already fixed in `MqttGatewayAPITest.java:274`:
```java
return ("{\"device\":\"" + deviceName + "\",\"type\":\"EBMPAPST_FFU\"}").getBytes(StandardCharsets.UTF_8);
```

---

## REST API for Manual Relation Creation (Advanced)

If you need to create custom relation types (e.g., "Created" instead of "Contains"), use the REST API:

### Endpoint: Create Relation

**Method**: `POST /api/relation`

**Request Body**:
```json
{
  "from": {
    "entityType": "DEVICE",
    "id": "gateway-uuid-here"

  "to": {
    "entityType": "DEVICE",
    "id": "device-uuid-here"

  "type": "Created",
  "typeGroup": "COMMON"
}
```

**Example**:
```bash
curl -X POST "https://demo.thingsboard.io/api/relation" \
  -H "X-Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from": {
      "entityType": "DEVICE",
      "id": "'$GATEWAY_ID'"
  
    "to": {
      "entityType": "DEVICE",
      "id": "'$DEVICE_ID'"
  
    "type": "Created",
    "typeGroup": "COMMON"
  }'
```

**Note**: Manual relation creation is typically NOT needed when using gateway auto-provisioning, as "Contains" relations are created automatically.

---

## Best Practices

### 1. Always Use Gateway Auto-Provisioning

✅ **Correct**:
```bash
DEVICE_CREATE_ON_START=false  # Let gateway provision devices
TEST_API=gateway              # Use gateway mode
```

❌ **Incorrect**:
```bash
DEVICE_CREATE_ON_START=true   # Creates via REST without relations
TEST_API=device               # Direct device mode (no gateway)
```

### 2. Real-World Device Behavior Pattern

Mimic actual IoT device lifecycle:

```
Device Bootup:
  1. Connect via gateway (v1/gateway/connect)
  2. Send initial attributes once (bootstrap data)
  3. Begin continuous telemetry stream

During Operation:
  - Send telemetry continuously (1-10 Hz typical)
  - Only send attributes on config changes or firmware updates
  - Do NOT send attributes on every cycle

Device Reboot:
  - Repeat bootup sequence
```

### 3. Device-Gateway Mapping Strategy

Our implementation uses round-robin distribution:

```java
private void mapDevicesToGatewayClientConnections() {
    int gatewayCount = mqttClients.size();
    for (int i = deviceStartIdx; i < deviceEndIdx; i++) {
        int deviceIdx = i - deviceStartIdx;
        int gatewayIdx = deviceIdx % gatewayCount;  // Round-robin
        DeviceClient client = new DeviceClient();
        client.setMqttClient(mqttClients.get(gatewayIdx));
        client.setDeviceName(getToken(false, i));
        client.setGatewayName(getToken(true, gatewayIdx));
        deviceClients.add(client);
    }
}
```

**Result** (for 60 devices, 2 gateways):
- GW00000000: DW00000000, DW00000002, DW00000004, ... (30 devices)
- GW00000001: DW00000001, DW00000003, DW00000005, ... (30 devices)

**Note**: This differs from the scenario configuration which uses sequential blocks:
- Scenario: GW00000000 → DW00000000-DW00000029, GW00000001 → DW00000030-DW00000059
- Implementation: Round-robin distribution

**Recommendation**: Update mapping logic to match scenario configuration for consistency.

---

## Implementation Checklist

- [x] Gateway devices created via provisioner
- [x] Gateway access tokens configured
- [x] `DEVICE_CREATE_ON_START=false` in `.env.ebmpapst-gateway`
- [x] `TEST_API=gateway` configured
- [x] Device provisioning via `v1/gateway/connect`
- [x] Device type specified in connect payload
- [x] Initial attributes sent after provisioning
- [x] Continuous telemetry during test phase
- [ ] Verify gateway relations in UI/API
- [ ] Update device-gateway mapping to match scenario configuration

---

## References

### ThingsBoard Documentation
- [Gateway MQTT API](https://thingsboard.io/docs/reference/gateway-mqtt-api/)
- [Entity Relations](https://thingsboard.io/docs/user-guide/entities-and-relations/)
- [Device Provisioning](https://thingsboard.io/docs/user-guide/device-provisioning/)
- [REST API](https://thingsboard.io/docs/reference/rest-api/)

### Project Documentation
- [GATEWAY_PROVISIONING.md](./GATEWAY_PROVISIONING.md)
- [CLAUDE.md](../CLAUDE.md)

### Codebase References
- `src/main/java/org/thingsboard/tools/service/gateway/MqttGatewayAPITest.java:267-275` - Device connect payload
- `src/main/java/org/thingsboard/tools/service/gateway/MqttGatewayAPITest.java:218-258` - Initial attributes
- `src/main/java/org/thingsboard/tools/service/GatewayBaseTestExecutor.java` - Test execution flow

---

## Solution Implemented: Automatic "Created" Relation Creation

### Implementation Summary

Based on the finding that gateway dashboards require **"Created" relations** (not "Contains") to display device information, we implemented an automatic relation creation system.

### New Components

#### 1. GatewayRelationManager Service

**File**: `src/main/java/org/thingsboard/tools/service/gateway/GatewayRelationManager.java`

- Creates bidirectional "Created" relations between gateways and devices
- Supports both synchronous and asynchronous operation
- Configurable via `gateway.createRelations` property
- Provides relation verification and deletion methods

**Key Method**:
```java
public int createGatewayDeviceRelations(Device gateway, List<Device> devices)
```

#### 2. Updated Test Flow

**Modified Files**:
- `src/main/java/org/thingsboard/tools/service/gateway/GatewayAPITest.java` - Added interface method
- `src/main/java/org/thingsboard/tools/service/gateway/MqttGatewayAPITest.java` - Implemented relation creation
- `src/main/java/org/thingsboard/tools/service/GatewayBaseTestExecutor.java` - Integrated into test lifecycle

**New Test Lifecycle**:
```
1. Connect Gateways
2. Warm Up Devices (provision via v1/gateway/connect) → Creates "Contains" relations
3. Create Gateway-Device Relations → Creates "Created" relations ★ NEW
4. Send Initial Attributes (bootstrap)
5. Run Continuous Telemetry Tests
```

### Configuration

#### `.env.ebmpapst-gateway`
```bash
GATEWAY_CREATE_RELATIONS=true  # Create "Created" relations for gateway dashboards
```

#### `tb-ce-performance-tests.yml`
```yaml
gateway:
  createRelations: "${GATEWAY_CREATE_RELATIONS:true}" # Create "Created" relations for gateway dashboards
```

### Usage

#### Automatic (Integrated into Performance Tests)

When running the performance tests, "Created" relations are automatically created after device provisioning:

```bash
./start-ebmpapst-gateway.sh
```

The test will:
1. Provision devices via Gateway MQTT API (creates "Contains" relations)
2. Automatically create "Created" relations via REST API
3. Display summary with verification instructions

#### Manual (Using Bash Script)

For existing deployments or manual relation creation:

```bash
# Set credentials
export REST_URL=https://demo.thingsboard.io
export REST_USERNAME=your-username
export REST_PASSWORD=your-password

# Run relation creation script
./create-gateway-relations.sh
```

The script will:
- Authenticate with ThingsBoard
- Fetch all gateway and device IDs
- Create bidirectional "Created" relations
- Display summary and verification steps

### Verification

After relations are created, verify in ThingsBoard UI:

1. **Gateway Relations Tab**:
   - Navigate to: Devices → GW00000000 → Relations
   - Should see BOTH "Contains" and "Created" relations to all devices
   - "Contains": Automatically created by v1/gateway/connect
   - "Created": Created by GatewayRelationManager

2. **Device Relations Tab**:
   - Navigate to: Devices → DW00000000 → Relations
   - Should see BOTH relation types back to gateway

3. **Gateway Dashboard**:
   - Open gateway dashboard
   - Device information should now be displayed correctly
   - Dashboard entity filters can now find devices via "Created" relations

### Technical Details

#### Why Both Relation Types?

- **"Contains"**: Automatically created by ThingsBoard's Gateway MQTT API
  - Represents the hierarchical ownership structure
  - Used by gateway connectivity logic

- **"Created"**: Required for gateway dashboards
  - Expected by dashboard entity aliases and filters
  - Enables device data aggregation and display

#### Relation Structure

```
Gateway (ID: xxx) ─┬─[Contains]─> Device (ID: yyy)
                   └─[Created]─> Device (ID: yyy)

Device (ID: yyy) ─┬─[Contains]─> Gateway (ID: xxx)
                  └─[Created]─> Gateway (ID: xxx)
```

Both relations are bidirectional, enabling queries from either direction.

### Troubleshooting

#### Issue: Relations Not Created

**Check**:
1. `GATEWAY_CREATE_RELATIONS=true` in `.env.ebmpapst-gateway`
2. Devices provisioned successfully (check warmup logs)
3. GatewayRelationManager bean available (check Spring logs)

**Solution**:
- Verify configuration
- Check REST API authentication
- Run manual script: `./create-gateway-relations.sh`

#### Issue: Dashboard Still Not Showing Devices

**Possible Causes**:
1. Dashboard entity alias configured for wrong relation type
2. Device type mismatch in dashboard filters
3. Relations created but dashboard not refreshed

**Solution**:
1. Check dashboard entity alias settings
2. Verify device type is "EBMPAPST_FFU"
3. Refresh dashboard or re-login

---

## Conclusion

**Key Takeaways**:

1. ✅ **Use Gateway MQTT API**: `v1/gateway/connect` for device provisioning
2. ✅ **Automatic "Contains" Relations**: Created by ThingsBoard during provisioning
3. ✅ **Automatic "Created" Relations**: Now implemented via GatewayRelationManager
4. ✅ **Set `DEVICE_CREATE_ON_START=false`**: Critical for gateway auto-provisioning
5. ✅ **Set `GATEWAY_CREATE_RELATIONS=true`**: Enables dashboard functionality
6. ✅ **Both Relation Types Required**: "Contains" for connectivity, "Created" for dashboards

**Implementation Status**:

- ✅ GatewayRelationManager service created
- ✅ Integration into test lifecycle complete
- ✅ Configuration properties added
- ✅ Bash script for manual execution available
- ✅ Code compiled successfully
- ⏳ Pending: Real-world testing and verification

**Next Steps**:

1. Run performance test with new relation creation: `./start-ebmpapst-gateway.sh`
2. Verify "Created" relations in ThingsBoard UI
3. Confirm gateway dashboard displays device information
4. Monitor logs for any relation creation errors
5. Document dashboard configuration if additional setup needed

---

**Last Updated**: 2025-10-29
**Author**: Generated by Claude Code with implementation by Claude Code Assistant
**Status**: ✅ Implementation Complete - Ready for Testing
