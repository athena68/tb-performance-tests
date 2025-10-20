# Project Status

**Last Updated**: 2025-10-19 (Fixed Gateway as DEVICE, not ASSET. Correct ThingsBoard architecture implemented.)

---

## Summary

ebmpapst FFU Performance Testing and Cleanroom Monitoring Dashboard implementation for ThingsBoard.

- **Server**: http://167.99.64.71:8080
- **Devices**: 60 FFU devices (DW00000000-DW00000059)
- **Gateway**: GW00000000
- **Test Mode**: Gateway-based auto-provisioning
- **Dashboard**: Basic table view (Option A - Simplified)

---

## Current Status

### ✓ Completed

1. **Gateway Auto-Provisioning** ✓
   - Fixed device type assignment (EBMPAPST_FFU)
   - Automatic attribute sending after provisioning
   - Real-world IoT device behavior implemented
   - 60 devices successfully provisioned

2. **Device Profile** ✓
   - EBMPAPST_FFU profile created
   - 42 attributes configured
   - 12 telemetry keys defined
   - Realistic ebmpapst specifications

3. **Performance Testing** ✓
   - Gateway mode working
   - 60 messages/second sustained
   - 24-hour test duration configured
   - Telemetry verified flowing

4. **Dashboard - Phase 1 (Simplified)** ✓
   - Table view with all 60 devices
   - Device names displayed
   - 6 telemetry columns (Speed, Setpoint, Pressure, Temp, Power, Hours)
   - Search and sort functionality
   - Pagination (20 devices/page)
   - URL: http://167.99.64.71:8080/dashboard/c44d7020-ab2e-11f0-af4d-97d7c19de825

5. **Documentation Consolidated** ✓
   - All guides moved to docs/ folder
   - Created comprehensive docs/GATEWAY_PROVISIONING.md
   - Archived old documentation
   - Updated README with links
   - Created status tracking (STATUS.md)

6. **Scenario-Based Provisioning** ✓
   - Configuration-driven hierarchy: Site → Building → Floor → Room → Gateway → Devices
   - Reflects real IoT architecture (devices connect through gateways)
   - Multiple scenarios supported (single-site, multi-site)
   - JSON-based configuration with locations, classifications
   - Python provisioner with full error handling
   - **Note**: Dashboards should be created manually via ThingsBoard UI

7. **Automated Test Configuration** ✓
   - Auto-generation of .env.ebmpapst-gateway from scenario
   - No manual configuration needed
   - Gateway and device counts automatically calculated
   - Message rates and test duration from scenario testConfig
   - Eliminates configuration mismatches

8. **Asset Attributes for Visualization** ✓
   - Building: address, email, phone, location (lat/long)
   - Room: floorPlan (image URL), classification, area
   - Device: xPos, yPos (position on floor plan)
   - Grid layout calculation with configurable spacing
   - Supports floor plan visualization in dashboards

9. **Scenario Validation** ✓
   - Validates totals match actual entity counts (warnings)
   - Enforces STRICT RULE: Exactly one gateway per room (error)
   - Validates device count matches start-end range
   - Clear error/warning messages with comparison table
   - Blocks provisioning on errors, asks confirmation on warnings
   - Prevents common configuration mistakes

---

### 🚧 In Progress

1. **Dashboard - Option A (Enhanced)**
   - Need to add: 4 metric cards
   - Need to add: 2 time series charts (Speed, Pressure)
   - Need to add: Alarms table
   - Need to add: Device drill-down state
   - Current: Basic table view only

---

### 📋 Pending

None - All core functionality completed!

---

## Quick Commands

### Verify Setup
```bash
./verify-current-setup.sh
```

### Run Performance Test
```bash
./start-ebmpapst-gateway.sh
```

### Clean Up Scenario
```bash
# Option 1: Clean using provisioned_entities.json (recommended)
./cleanup-scenario.py

# Option 2: Clean by pattern (if you don't have the JSON file)
./cleanup-scenario.py --pattern --assets "Hanoi" "Building A" "Floor 5"

# Option 3: Clean only devices/gateways (old script)
./cleanup-test-devices.sh
```

### Provision Full Hierarchy from Scenario
```bash
# Step 1: Provision Hanoi cleanroom scenario (60 devices, 2 gateways)
# Automatically generates .env.ebmpapst-gateway configuration AND sets gateway credentials
./provision-scenario.py test-scenarios/scenario-hanoi-cleanroom.json

# Step 2: Run performance test (that's it!)
./start-ebmpapst-gateway.sh

# Alternative scenarios:
# - Provision multi-site scenario (70 devices, 5 gateways, 2 locations)
./provision-scenario.py test-scenarios/scenario-multi-site.json

# View available scenarios
ls test-scenarios/*.json

# What gets created:
# - Site → Building → Floor → Room → Gateway → Devices hierarchy
# - Building attributes: address, email, phone, location
# - Room attributes: floorPlan, classification, area
# - Device attributes: xPos, yPos (grid positions - relative 0.0 to 1.0)
# - Auto-generated .env.ebmpapst-gateway file
# - Gateway credentials automatically set (token = gateway name)
# - Entity IDs saved to /tmp/provisioned_entities.json
```

### List FFU Devices
```bash
./list-ffu-devices.sh
```

### Check Device Types
```bash
./check-device-types.sh
```

---

## Key Files

### Scripts
- `provision-scenario.py` - **NEW:** Provision full hierarchy from JSON scenario (auto-sets gateway credentials)
- `setup-gateway-credentials.sh` - **Optional:** Manually fix gateway credentials (not needed for normal workflow)
- `cleanup-scenario.py` - **NEW:** Clean up scenario (assets + devices)
- `verify-current-setup.sh` - Verify all devices operational
- `start-ebmpapst-gateway.sh` - Run gateway performance test (supports multiple gateways)
- `cleanup-test-devices.sh` - Remove test devices only (not assets)
- `scripts/archive/` - Deprecated bash provisioning scripts

### Configuration
- `.env.ebmpapst-gateway` - Gateway mode configuration
- `src/main/resources/device-profiles/ebmpapst_ffu.json` - Device profile

### Test Scenarios
- `test-scenarios/scenario-hanoi-cleanroom.json` - Single building, 2 rooms, 60 devices
- `test-scenarios/scenario-multi-site.json` - Multi-building, 5 rooms, 70 devices
- `test-scenarios/README.md` - Scenario format and customization guide

### Code
- `src/main/java/org/thingsboard/tools/service/gateway/MqttGatewayAPITest.java` - Gateway test implementation
- `src/main/java/org/thingsboard/tools/service/msg/ebmpapstFfu/` - FFU message generators

### Dashboards
- `dashboards/cleanroom_working.json` - Reference template for manual dashboard creation
- `dashboards/archive/` - Deprecated automated dashboard JSONs (not recommended)
- **Note**: Dashboards should be created manually via ThingsBoard UI for best results

### Documentation
- `docs/GATEWAY_PROVISIONING.md` - Complete provisioning guide
- `CLAUDE.md` - Project overview for AI assistants
- `README.md` - User guide
- `STATUS.md` - This file

---

## Gateway Credentials (Auto-Configured!)

### How It Works

Gateway credentials are **automatically configured** during provisioning:

**What Happens:**
- When `provision-scenario.py` creates a gateway device
- It immediately sets the access token to match the gateway name
- Example: Gateway "GW00000000" gets access token "GW00000000"
- This is done for ALL gateways in the scenario

**No Manual Step Required!**

The `setup-gateway-credentials.sh` script is still available for special cases (e.g., fixing existing gateways), but it's **not needed** for normal provisioning workflow.

**What You'll See:**
```
✓ Gateway credentials: GW00000000 → token: GW00000000
✓ Gateway credentials: GW00000001 → token: GW00000001
```

**Technical Details:**
- Gateway devices created with `additionalInfo: {"gateway": true}`
- Credentials API called immediately after device creation
- Each gateway's credentialsId set to match device name
- Performance test can connect using gateway name as token

---

## Issues and Fixes

### Fixed Issues

1. **Gateway Relations Empty** ✓
   - **Problem**: Devices created via REST API had no gateway relations
   - **Fix**: Set `DEVICE_CREATE_ON_START=false` to enable auto-provisioning

2. **Device Type "default"** ✓
   - **Problem**: Auto-provisioned devices had type "default"
   - **Fix**: Added device type to gateway connect payload
   - **Code**: Modified `getData()` in `MqttGatewayAPITest.java`

3. **Missing Attributes** ✓
   - **Problem**: Only telemetry visible, no attributes
   - **Fix**: Added `sendInitialAttributes()` after device provisioning
   - **Behavior**: Mimics real IoT devices (bootstrap attributes once)

4. **Dashboard No Devices** ✓
   - **Problem**: Entity filter used deviceType but devices had type "default"
   - **Fix**: Changed filter to entityName pattern matching "DW"

5. **Dashboard No Device Names** ✓
   - **Problem**: Table didn't show device name column
   - **Fix**: Set `displayEntityName: true` in widget settings

6. **Multi-Gateway Connection Failure + Missing Device (Critical)** ✓
   - **Problem**: Only GW00000000 connected, GW00000001 inactive. Only 59/60 devices created (missing DW00000059).
   - **Root Cause**: Off-by-one errors in `.env.ebmpapst-gateway` for both gateways and devices
   - **Details**:
     - **Gateway Issue**: `GATEWAY_END_IDX=1` only connects gateway index 0
     - **Device Issue**: `DEVICE_END_IDX=59` only creates devices 0-58 (59 devices)
     - Java code uses `for (i = START; i < END; i++)` (END is exclusive, like Python range)
     - With `GATEWAY_START_IDX=0, GATEWAY_END_IDX=1`: only connects GW00000000
     - With `DEVICE_START_IDX=0, DEVICE_END_IDX=59`: only creates 0-58 (59 devices)
   - **Fix**:
     - **Gateways**: Changed `GATEWAY_END_IDX=2` (was 1)
     - **Devices**: Changed `DEVICE_END_IDX=60` (was 59)
     - Updated `provision-scenario.py` lines 563 and 602
     - Formula: `END_IDX = count` (not `count - 1`) for exclusive end ranges
   - **Result**: Both gateways connect, all 60 devices created, distributed evenly (alternating pattern)
   - **Location**: `provision-scenario.py:563,602` and `.env.ebmpapst-gateway:29,36`

---

## Next Steps

### Dashboard Creation (Manual via ThingsBoard UI)
1. **Option A (Flat View)**: Create dashboard showing all 60 FFU devices
   - Add entity table widget with all devices
   - Add metric cards, time series charts, alarms table
   - Use `cleanroom_working.json` as reference

2. **Option B (Hierarchical)**: Create dashboard organized by rooms
   - Create separate states or sections for each room
   - Show Room R501 devices (DW00000000-029)
   - Show Room R502 devices (DW00000030-059)
   - Add navigation between rooms

### Optional Enhancements
1. Add metric cards (Total Devices, Avg Speed, Avg Pressure, Avg Power)
2. Add time series charts (Speed over time, Pressure over time)
3. Add alarms and notifications
4. Add custom widgets for room navigation

---

## Performance Metrics

### Current Setup (Hanoi Cleanroom Scenario)
- **Hierarchy**: 1 Site → 1 Building → 1 Floor → 2 Rooms → 2 Gateways → 60 Devices
- **Message Rate**: 60 messages/second (1 msg/device/second)
- **Test Duration**: 24 hours (configurable via scenario)
- **Telemetry Keys**: 12 per device
- **Attributes per Entity**:
  - Building: 5 (address, email, phone, latitude, longitude)
  - Room: 3 (floorPlan, classification, area_sqm)
  - Gateway: 1 (protocol)
  - Device: 44 (42 spec attributes + xPos + yPos)

### Multi-Site Scenario (Available)
- **Hierarchy**: 1 Site → 2 Buildings → 3 Floors → 5 Rooms → 5 Gateways → 70 Devices
- **Geographic**: Hanoi (50 devices) + Ho Chi Minh City (20 devices)
- **Message Rate**: 70 messages/second (configurable)

---

## Contact / Notes

- Test server is shared environment
- Use cleanup script to remove test devices when done
- Dashboard URL may change if recreated
- Gateway token must be "GW00000000" for tests to work

---

## Correct ThingsBoard Architecture

### IMPORTANT: Gateway is a Device, Not an Asset!

In ThingsBoard:
- **Assets**: Site, Building, Floor, Room (organizational hierarchy)
- **Gateway**: Special **DEVICE** with `"gateway": true` flag in additionalInfo
- **Regular Devices**: FFU devices that connect through the gateway

**Correct Hierarchy:**
```
Site (ASSET)
  → Building (ASSET)
    → Floor (ASSET)
      → Room (ASSET)
        → Gateway (DEVICE with gateway=true)
          → FFU Devices (DEVICE)
```

**Relations:**
- Room (ASSET) → Gateway (DEVICE): "Contains" relation
- Gateway (DEVICE) → Device (DEVICE): "Contains" relation

This reflects real IoT architecture where:
- FFU devices cannot connect directly to ThingsBoard
- FFUs connect to a physical gateway device in the room
- Gateway aggregates and forwards data to ThingsBoard via MQTT

---

## Recent Enhancements (2025-10-19)

### 1. Fixed Gateway Architecture
- Gateways now created as DEVICE (not ASSET)
- `additionalInfo: {"gateway": true}` flag set correctly
- Relations fixed: Room (ASSET) → Gateway (DEVICE) → Devices (DEVICE)
- Type: "Gateway" (can be changed to "default" if preferred)

### 2. Automated .env Configuration Generation
- Provisioner now auto-generates `.env.ebmpapst-gateway` from scenario JSON
- Includes ThingsBoard server config, MQTT settings, test parameters
- Gateway and device counts calculated automatically
- Eliminates manual configuration and potential mismatches

### Enhanced Asset Attributes
**Building Attributes:**
- `address` (string) - Full physical address
- `email` (string) - Facility contact email
- `phone` (string) - Facility contact phone
- `latitude` (number) - Geographic latitude
- `longitude` (number) - Geographic longitude

**Room Attributes:**
- `floorPlan` (string) - URL to floor plan image
- `classification` (string) - ISO cleanroom classification
- `area_sqm` (number) - Room area in square meters

**Device Attributes:**
- `xPos` (number) - X position on floor plan (relative coordinates: 0.0 to 1.0)
- `yPos` (number) - Y position on floor plan (relative coordinates: 0.0 to 1.0)
- Calculated automatically using grid layout configuration
- Example: xPos=0.35 means 35% from left edge (ThingsBoard standard)

### Grid Layout Calculation
- Devices positioned automatically in configurable grid using **relative coordinates** (0.0 to 1.0)
- Parameters:
  - `gridColumns`: Number of columns (e.g., 6)
  - `gridRows`: Number of rows (e.g., 5) - optional, for reference
  - `startX`: Starting X position as percentage (0.1 = 10% from left edge)
  - `startY`: Starting Y position as percentage (0.1 = 10% from top edge)
  - `spacingX`: Horizontal spacing as percentage (0.15 = 15% spacing between columns)
  - `spacingY`: Vertical spacing as percentage (0.15 = 15% spacing between rows)
- Example: 30 devices in 6x5 grid
  - Row 1: (0.1, 0.1), (0.25, 0.1), (0.4, 0.1), (0.55, 0.1), (0.7, 0.1), (0.85, 0.1)
  - Row 2: (0.1, 0.25), (0.25, 0.25), etc.
- **Why relative coordinates?** Resolution-independent, works with any floor plan image size (ThingsBoard standard)

### Workflow Improvements
**Before:**
1. Run provisioner
2. Manually edit .env file
3. Configure gateway indices, device counts
4. Risk of configuration mismatch

**Now:**
1. Edit scenario JSON (or use existing)
2. Run provisioner once
3. Ready to test!

### 4. Scenario Validation (2025-10-19)

**Validation Rules:**
- **STRICT RULE (ERROR)**: Exactly one gateway per room
  - Reflects real-world constraint: one physical gateway per room
  - Prevents invalid configurations
  - Blocks provisioning if violated

- **Totals Validation (WARNING)**: Declared totals must match actual counts
  - Sites, buildings, floors, rooms, gateways, devices
  - Shows comparison table with declared vs actual
  - Allows proceeding with user confirmation

- **Device Count Validation (WARNING)**: count field must match start-end range
  - Example: start=0, end=9 implies count=10
  - Helps catch copy-paste errors

**Validation Output:**
```
Entity Type     Declared     Actual       Status
------------------------------------------------------------
Sites           1            1            ✓ OK
Buildings       2            1            ⚠ MISMATCH
Gateways        1            2            ⚠ MISMATCH
```

**Error Handling:**
- Errors → Block provisioning immediately
- Warnings → Ask user to confirm or fix totals
- All OK → Proceed to provisioning

---

**Status**: ✓ Full automation complete - One-step provisioning with zero manual configuration and validation. Create dashboards manually via ThingsBoard UI for best results.
