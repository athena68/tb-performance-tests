# Gateway Mode Configuration Guide

This guide explains how to configure the ebmpapst FFU performance test to use an **existing ThingsBoard gateway** instead of direct device connections.

## Architecture Comparison

### Direct Device Mode (Default)
```
[Test Tool] → MQTT → [ThingsBoard Server]
    ↓
[50 FFU Devices connect directly]
```

### Gateway Mode (Your Setup)
```
[Test Tool] → MQTT → [Your Gateway] → [ThingsBoard Server]
                           ↓
                     [50 FFU Devices]
```

**Benefits of Gateway Mode:**
- Centralized connection management
- Reduced network overhead
- Simulates real industrial deployment
- Gateway can be on-premises while ThingsBoard is in cloud

---

## Prerequisites

1. **Your gateway must be already connected** to ThingsBoard server (167.99.64.71)
2. **Gateway must have MQTT connection active**
3. You need **admin access** to ThingsBoard UI to modify gateway credentials

---

## Step-by-Step Setup

### Step 1: Configure Your Gateway Token

The performance test expects gateway tokens in format: `GW00000000`, `GW00000001`, etc.

**On ThingsBoard UI:**

1. Login to: http://167.99.64.71:8080
2. Navigate to: **Devices** → Find your gateway
3. Click on your gateway device
4. Click **"Manage credentials"** button
5. Change **Access token** to: `GW00000000`
6. Click **"Save"**

![Gateway Token Configuration](https://thingsboard.io/docs/user-guide/resources/gateway-credentials.png)

### Step 2: Reconnect Your Gateway

After changing the token, your gateway needs to reconnect:

**Option A: If gateway is running locally:**
```bash
# Restart your gateway service with new token
sudo systemctl restart tb-gateway
# OR
docker restart tb-gateway
```

**Option B: If gateway is in your application:**
```python
# Update gateway connection config
GATEWAY_TOKEN = "GW00000000"
```

**Verify Connection:**
- Go to: Devices → Your Gateway
- Check **"Last Activity Time"** - should update to current time
- Status should show as **"Active"**

### Step 3: Configure Test Environment

Use the pre-configured gateway environment:

```bash
# Review/edit configuration
nano .env.ebmpapst-gateway

# Key settings:
TEST_API=gateway              # Enable gateway mode
GATEWAY_CREATE_ON_START=false # Use existing gateway
DEVICE_CREATE_ON_START=true   # Create child devices
GATEWAY_START_IDX=0           # Gateway index 0
GATEWAY_END_IDX=1             # Only 1 gateway
DEVICE_START_IDX=0            # First FFU device
DEVICE_END_IDX=50             # 50 FFU devices total
```

### Step 4: Run Gateway Test

```bash
./start-ebmpapst-gateway.sh
```

The script will:
1. ✓ Check configuration
2. ✓ Confirm gateway is ready
3. ✓ Create 50 FFU devices in ThingsBoard
4. ✓ Connect test tool to gateway (token: GW00000000)
5. ✓ Send telemetry through gateway
6. ✓ All data appears under each FFU device in ThingsBoard

---

## Configuration Options

### `.env.ebmpapst-gateway` Key Parameters:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `TEST_API` | `gateway` | **REQUIRED**: Enable gateway mode |
| `GATEWAY_CREATE_ON_START` | `false` | Don't create gateway (already exists) |
| `GATEWAY_START_IDX` | `0` | Your gateway uses token GW00000000 |
| `GATEWAY_END_IDX` | `1` | Only 1 gateway |
| `DEVICE_CREATE_ON_START` | `true` | Create 50 FFU devices as children |
| `DEVICE_START_IDX` | `0` | First device index |
| `DEVICE_END_IDX` | `50` | Last device index (50 devices) |
| `MESSAGES_PER_SECOND` | `50` | Message rate |
| `DURATION_IN_SECONDS` | `300` | Test duration (5 min) |

### Multiple Gateways (Advanced)

If you want to test with **multiple gateways**:

```bash
# Configure 3 gateways
GATEWAY_START_IDX=0
GATEWAY_END_IDX=3
GATEWAY_CREATE_ON_START=true  # Let test create gateways

# Gateway tokens will be:
# GW00000000, GW00000001, GW00000002

# Distribute devices across gateways
DEVICE_START_IDX=0
DEVICE_END_IDX=150  # 50 devices per gateway
```

---

## Verification Steps

After running the test, verify everything is working:

### 1. Check Gateway Connection

```bash
# On ThingsBoard UI:
Devices → Your Gateway

✓ Status: Active
✓ Last Activity Time: Within last minute
✓ Telemetry: Should see incoming messages
```

### 2. Check FFU Devices Created

```bash
# On ThingsBoard UI:
Devices → All

✓ Should see 50 new devices:
  - DW00000000, DW00000001, ..., DW00000049
✓ Device Profile: EBMPAPST_FFU
✓ Each device has green "Active" status
```

### 3. Verify Device Relations

```bash
# On ThingsBoard UI:
Devices → Your Gateway → Relations tab

✓ Should see 50 devices listed under "Contains" relationship
✓ Each device shows type: "Device"
✓ Direction: Outbound
```

### 4. Check Telemetry Data

```bash
# On ThingsBoard UI:
Devices → DW00000000 (any FFU device) → Latest telemetry

✓ Should see ebmpapst FFU data:
  - actualSpeed
  - dcLinkVoltage
  - dcLinkCurrent
  - powerConsumption
  - differentialPressure
  - motorTemperature
  - operatingStatus
  - etc.
```

### 5. Check Attributes

Run attributes population:
```bash
# Set TEST_TELEMETRY=false in .env.ebmpapst-gateway
export TEST_TELEMETRY=false
./start-ebmpapst-gateway.sh

# Or use the dedicated script
./populate-ebmpapst-attributes.sh
```

Then verify:
```bash
# On ThingsBoard UI:
Devices → DW00000000 → Attributes tab

✓ Should see attributes:
  - fanModel
  - manufacturer
  - firmwareVersion
  - serialNumber
  - modbusAddress
  - etc.
```

---

## Troubleshooting

### Problem: "Gateway not connected"

**Solution:**
```bash
# 1. Check gateway token matches
ThingsBoard UI → Gateway → Credentials
Should be: GW00000000

# 2. Check gateway service is running
sudo systemctl status tb-gateway
# OR
docker ps | grep gateway

# 3. Check gateway logs
journalctl -u tb-gateway -f
# OR
docker logs -f tb-gateway

# 4. Verify MQTT connection
MQTT_HOST=167.99.64.71
MQTT_PORT=1883
```

### Problem: "Devices not appearing"

**Solution:**
```bash
# Verify DEVICE_CREATE_ON_START=true
cat .env.ebmpapst-gateway | grep DEVICE_CREATE_ON_START

# Check REST API credentials
REST_URL=http://167.99.64.71:8080
REST_USERNAME=tenant@thingsboard.org
REST_PASSWORD=your-password

# Check test logs for errors
mvn spring-boot:run | tee test-gateway.log
```

### Problem: "No telemetry data"

**Solution:**
```bash
# 1. Verify TEST_API=gateway
cat .env.ebmpapst-gateway | grep TEST_API

# 2. Check gateway is receiving data
ThingsBoard UI → Gateway → Latest telemetry
# Should see activity

# 3. Verify TEST_TELEMETRY=true for telemetry
cat .env.ebmpapst-gateway | grep TEST_TELEMETRY

# 4. Check message rate isn't too high
MESSAGES_PER_SECOND=50  # Start low, increase gradually
```

### Problem: "Gateway token format error"

**Error:** `Gateway token must be exactly GW00000000`

**Solution:**
```bash
# The token MUST be exactly 10 characters:
# - "GW" prefix
# - 8 digits with leading zeros
# ✓ Correct: GW00000000
# ✗ Wrong: GW0, gateway-token, GW000000000
```

---

## Advanced Configuration

### Use Custom Gateway Token (Code Modification Required)

If you want to keep your current gateway token instead of renaming to `GW00000000`, you need to modify the code:

**File:** `src/main/java/org/thingsboard/tools/service/shared/AbstractAPITest.java`

```java
// Line 293 - Replace:
protected String getToken(boolean isGateway, int token) {
    return (isGateway ? "GW" : "DW") + String.format("%8d", token).replace(" ", "0");
}

// With:
protected String getToken(boolean isGateway, int token) {
    if (isGateway && token == 0) {
        return System.getenv().getOrDefault("GATEWAY_TOKEN", "GW00000000");
    }
    return (isGateway ? "GW" : "DW") + String.format("%8d", token).replace(" ", "0");
}
```

Then set environment variable:
```bash
export GATEWAY_TOKEN="your_actual_gateway_token"
mvn spring-boot:run
```

**Note:** This requires rebuilding the project.

---

## Performance Considerations

### Gateway Mode vs Direct Mode:

| Aspect | Direct Mode | Gateway Mode |
|--------|-------------|--------------|
| **Connections** | 50 MQTT connections | 1 MQTT connection |
| **Network** | 50x traffic to server | 1x traffic to server |
| **Latency** | Lower | Slightly higher (gateway hop) |
| **Scalability** | Limited by connections | Better (thousands of devices) |
| **Real-world** | Not typical | Production-like |

### Recommended Settings for Gateway Mode:

```bash
# For 50 devices through 1 gateway:
MESSAGES_PER_SECOND=50      # 1 msg/device/sec
DURATION_IN_SECONDS=300     # 5 minutes

# For 500 devices through 1 gateway:
MESSAGES_PER_SECOND=100     # Lower rate per device
DURATION_IN_SECONDS=600     # 10 minutes

# For 5000 devices through multiple gateways:
GATEWAY_END_IDX=10          # 10 gateways
DEVICE_END_IDX=5000         # 500 devices per gateway
MESSAGES_PER_SECOND=1000    # Distributed load
```

---

## Data Flow Diagram

### Gateway MQTT Topic Structure:

```
Gateway publishes to topic:
v1/gateway/telemetry

Payload format:
{
  "DW00000000": [{
    "ts": 1234567890000,
    "values": {
      "actualSpeed": 1547,
      "dcLinkVoltage": 398.5,
      ...
    }
  }],
  "DW00000001": [{
    "ts": 1234567890000,
    "values": { ... }
  }]
}
```

ThingsBoard automatically:
1. Receives message on gateway
2. Parses device names (DW00000000, DW00000001, etc.)
3. Routes telemetry to respective devices
4. Updates device "Last Activity Time"
5. Triggers alarms if conditions met

---

## Next Steps

1. ✅ **Setup Complete** - Gateway mode configured
2. ✅ **Run Test** - Execute `./start-ebmpapst-gateway.sh`
3. ⬜ **Monitor Performance** - Check ThingsBoard system stats
4. ⬜ **Scale Testing** - Increase device count gradually
5. ⬜ **Production Deployment** - Use learnings for real gateway setup

---

## Support

For issues:
1. Check logs: `mvn spring-boot:run | tee gateway-test.log`
2. Verify gateway connectivity: ThingsBoard UI → Gateway device
3. Review configuration: `cat .env.ebmpapst-gateway`
4. Consult main documentation: `README.md`, `FFU_TEST_EBMPAPST.md`
