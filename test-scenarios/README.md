# Test Scenarios

Configuration-based test scenarios for provisioning ThingsBoard hierarchies.

## Hierarchy Architecture

The correct IoT hierarchy that reflects real-world deployment:

```
Site (ASSET)
└── Building (ASSET - with lat/long location)
    └── Floor (ASSET)
        └── Room (ASSET - with ISO classification, area)
            └── Gateway (DEVICE with "gateway": true flag)
                └── FFU Devices (DEVICE - connected to gateway)
```

### IMPORTANT: Gateway is a Device, Not an Asset!

In ThingsBoard:
- **Site, Building, Floor, Room** = ASSETS (organizational hierarchy)
- **Gateway** = Special DEVICE with `additionalInfo: {"gateway": true}`
- **FFU Devices** = Regular DEVICES

**Why this matters:**
- Gateway is physical hardware that connects to ThingsBoard
- FFUs connect to the gateway, not directly to ThingsBoard
- Gateway uses ThingsBoard Gateway API to auto-provision devices
- This reflects real industrial IoT architecture

### Why This Matters

**Technical Reality:**
- FFU devices cannot directly connect to ThingsBoard server
- FFUs connect to a **Gateway** via local network (Modbus, etc.)
- Gateway aggregates data and forwards to ThingsBoard via MQTT
- A gateway is physically located in a **single room**
- Devices connected to one gateway **cannot be separated across rooms**

**Operational Reality:**
- Buildings have physical locations (latitude/longitude)
- Rooms have classifications (ISO 5, ISO 6, ISO 7, etc.)
- Gateways serve a specific physical area
- This hierarchy enables proper asset management and reporting

---

## Scenario Validation

The provisioner validates scenarios before creating entities:

### Validation Rules

**STRICT RULE (ERROR)**: Exactly one gateway per room
- ❌ **Invalid**: Room with 0 gateways or 2+ gateways
- ✓ **Valid**: Room with exactly 1 gateway
- **Reason**: Reflects real-world constraint (one physical gateway per room)
- **Action**: Provisioning blocked if violated

**Totals Field (WARNING)**: Must match actual entity counts
- Checks: sites, buildings, floors, rooms, gateways, devices
- Shows comparison table: Declared vs Actual
- **Action**: Asks user to confirm or fix totals

**Device Count (WARNING)**: count field must match start-end range
- Example: `start: 0, end: 9` → `count: 10` ✓
- Example: `start: 0, end: 9` → `count: 15` ⚠ (mismatch)
- **Action**: Warning displayed, user can proceed

### Example Validation Output

```
============================================================
Validating Scenario Configuration
============================================================

Entity Type     Declared     Actual       Status
------------------------------------------------------------
Sites           1            1            ✓ OK
Buildings       1            1            ✓ OK
Floors          1            1            ✓ OK
Rooms           2            2            ✓ OK
Gateways        2            2            ✓ OK
Devices         60           60           ✓ OK

✓ Validation passed - all checks OK
```

### Common Validation Errors

**Error: Multiple gateways per room**
```
✗ Errors (1):
  - Room 'Room 101' has 2 gateways (must have exactly 1)

❌ VALIDATION FAILED - Cannot proceed with provisioning
```
**Fix**: Remove extra gateways or split into separate rooms

**Warning: Totals mismatch**
```
⚠ Warnings (2):
  - Total buildings: declared=2, actual=1
  - Total devices: declared=10, actual=5

Proceed with provisioning? (yes/no):
```
**Fix**: Update totals field to match actual counts or proceed anyway

---

## Available Scenarios

### 1. scenario-hanoi-cleanroom.json

**Single Building, Basic Setup**
- 1 Site: Hanoi Industrial Park
- 1 Building: Building A (Cleanroom Facility)
- 1 Floor: Floor 5
- 2 Rooms: R501 (ISO 5), R502 (ISO 6)
- 2 Gateways: GW00000000, GW00000001
- 60 FFU Devices: DW00000000-DW00000059

**Use Case:** Single facility testing, initial setup, development

**Device Distribution:**
- Room R501 → GW00000000 → 30 FFUs (DW00000000-029)
- Room R502 → GW00000001 → 30 FFUs (DW00000030-059)

### 2. scenario-multi-site.json

**Multi-Building, Advanced Setup**
- 1 Site: Vietnam Manufacturing Sites
- 2 Buildings:
  - Hanoi Building A (Lat: 21.0285, Long: 105.8542)
    - Floor 3: 2 rooms, 2 gateways, 20 devices
    - Floor 5: 2 rooms, 2 gateways, 30 devices
  - HCMC Building B (Lat: 10.7769, Long: 106.7009)
    - Floor 2: 1 room, 1 gateway, 20 devices
- 5 Gateways total
- 70 FFU Devices total

**Use Case:** Multi-site deployment, geographic distribution, scalability testing

---

## Scenario File Format

```json
{
  "scenarioName": "Descriptive Name",
  "description": "What this scenario tests",
  "site": {
    "name": "Site Name",
    "type": "Site",
    "location": {
      "latitude": 21.0285,
      "longitude": 105.8542
  
    "address": "Physical address"

  "buildings": [
    {
      "name": "Building Name",
      "type": "Building",
      "label": "Building Label",
      "location": {
        "latitude": 21.0285,
        "longitude": 105.8542
    
      "floors": [
        {
          "name": "Floor X",
          "type": "Floor",
          "label": "Floor Description",
          "rooms": [
            {
              "name": "Room RXX",
              "type": "Room",
              "label": "ISO X Cleanroom",
              "classification": "ISO X",
              "area_sqm": 100,
              "gateways": [
                {
                  "name": "GWXXXXXXXX",
                  "type": "Gateway",
                  "label": "Gateway Description",
                  "protocol": "MQTT",
                  "devices": {
                    "prefix": "DW",
                    "start": 0,
                    "end": 29,
                    "count": 30,
                    "layout": "grid",
                    "gridColumns": 6,
                    "gridRows": 5,
                    "startX": 0.1,
                    "startY": 0.1,
                    "spacingX": 0.15,
                    "spacingY": 0.15
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
    "sites": 1,
    "buildings": 1,
    "floors": 1,
    "rooms": 2,
    "gateways": 2,
    "devices": 60
  }
}
```

---

## Device Positioning (Floor Plan Coordinates)

Devices are automatically positioned on floor plans using **relative coordinates** (0.0 to 1.0 range).

### Why Relative Coordinates?
- **Resolution-independent**: Works with any floor plan image size
- **ThingsBoard standard**: Official ThingsBoard widgets use this format
- Example: `xPos: 0.35` means 35% from left edge, `yPos: 0.6` means 60% from top edge

### Grid Layout Parameters

```json
"devices": {
  "layout": "grid",           // Layout type (currently only "grid" supported)
  "gridColumns": 6,            // Number of columns in the grid
  "gridRows": 5,               // Number of rows (optional, for reference)
  "startX": 0.1,               // Start at 10% from left edge
  "startY": 0.1,               // Start at 10% from top edge
  "spacingX": 0.15,            // 15% horizontal spacing between devices
  "spacingY": 0.15             // 15% vertical spacing between devices
}
```

### Example: 6-Column Grid

For 30 devices in a 6-column grid with the above parameters:

**Row 1 (devices 0-5):**
- Device 0: (0.1, 0.1)   - Top-left
- Device 1: (0.25, 0.1)  - 0.1 + 0.15
- Device 2: (0.4, 0.1)   - 0.1 + 2×0.15
- Device 3: (0.55, 0.1)  - 0.1 + 3×0.15
- Device 4: (0.7, 0.1)   - 0.1 + 4×0.15
- Device 5: (0.85, 0.1)  - 0.1 + 5×0.15

**Row 2 (devices 6-11):**
- Device 6: (0.1, 0.25)  - Same X as device 0, Y incremented by spacingY
- Device 7: (0.25, 0.25)
- ...and so on

### Customizing Positions

Adjust these parameters to fit your floor plan:
- **Dense placement**: `spacingX: 0.1, spacingY: 0.1` (10% spacing)
- **Sparse placement**: `spacingX: 0.2, spacingY: 0.2` (20% spacing)
- **More columns**: `gridColumns: 8` for wider rooms
- **Offset from edge**: `startX: 0.15, startY: 0.15` to start further from edges

---

## Usage

### Provision a Scenario

```bash
# Using the Python provisioner
./provision-scenario.py test-scenarios/scenario-hanoi-cleanroom.json

# With custom credentials
./provision-scenario.py test-scenarios/scenario-hanoi-cleanroom.json \
  --url https://your-thingsboard-server.com \
  --username your-email@domain.com \
  --password your-password

# Or using credentials.json (recommended)
./provision-scenario.py test-scenarios/scenario-hanoi-cleanroom.json
```

### What Gets Created

1. **Assets** (hierarchy):
   - Site asset with location attributes
   - Building assets with location attributes
   - Floor assets
   - Room assets with classification and area attributes
   - Gateway assets with protocol attributes

2. **Devices**:
   - FFU devices with type EBMPAPST_FFU
   - Named according to scenario (e.g., DW00000000-029)

3. **Relations**:
   - Site → Building (Contains)
   - Building → Floor (Contains)
   - Floor → Room (Contains)
   - Room → Gateway (Contains)
   - Gateway → Device (Contains)

4. **Output**:
   - All entity IDs saved to `/tmp/provisioned_entities.json`
   - Can be used for dashboard creation or testing

---

## Creating Custom Scenarios

### Example: Small Lab Setup

```json
{
  "scenarioName": "Research Lab",
  "description": "Small research facility with 1 cleanroom",
  "site": {
    "name": "University Research Center",
    "type": "Site",
    "location": {"latitude": 21.0285, "longitude": 105.8542},
    "address": "University Campus"

  "buildings": [
    {
      "name": "Research Building",
      "type": "Building",
      "label": "Nanotechnology Lab",
      "location": {"latitude": 21.0285, "longitude": 105.8542},
      "floors": [
        {
          "name": "Floor 1",
          "type": "Floor",
          "label": "Lab Floor",
          "rooms": [
            {
              "name": "Lab 101",
              "type": "Room",
              "label": "ISO 5 Cleanroom",
              "classification": "ISO 5",
              "area_sqm": 50,
              "gateways": [
                {
                  "name": "GW-LAB-101",
                  "type": "Gateway",
                  "label": "Lab 101 Gateway",
                  "protocol": "MQTT",
                  "devices": {
                    "prefix": "FFU-LAB",
                    "start": 1,
                    "end": 10,
                    "count": 10
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
    "sites": 1,
    "buildings": 1,
    "floors": 1,
    "rooms": 1,
    "gateways": 1,
    "devices": 10
  }
}
```

### Tips for Custom Scenarios

1. **Device Naming:**
   - Use descriptive prefixes: `DW`, `FFU`, `FILTER`, etc.
   - Include location codes for multi-site: `DW-HN-F5-R501-`
   - Zero-pad numbers for proper sorting

2. **Gateway Placement:**
   - One gateway per room is typical
   - Gateway name should indicate location
   - 10-50 devices per gateway is realistic

3. **Room Classification:**
   - ISO 5: Highest cleanliness (pharmaceutical, microelectronics)
   - ISO 6: High cleanliness (medical devices)
   - ISO 7: Moderate cleanliness (general manufacturing)
   - ISO 8: Basic cleanliness (assembly)

4. **Location Coordinates:**
   - Use actual building coordinates for realistic testing
   - Helps with geographic dashboards and reporting
   - Can be used for location-based analytics

---

## Migration from Old Setup

If you have existing devices from the old hierarchy (without Site/Gateway):

**Old Hierarchy:**
```
Building → Floor → Room → Devices (direct)
```

**New Hierarchy:**
```
Site → Building → Floor → Room → Gateway → Devices
```

**Migration Steps:**
1. Create new scenario with proper hierarchy
2. Provision new assets (Site, Gateway)
3. Update device relations to point to Gateway
4. Remove old direct Room→Device relations
5. Test dashboard queries with new hierarchy

---

## Performance Considerations

**Recommended Limits per Scenario:**
- Max devices per gateway: 50
- Max gateways per room: 2-3
- Max rooms per floor: 10
- Max floors per building: 20
- Max buildings per site: 10

**Why These Limits:**
- Dashboard query performance
- Gateway capacity (real hardware limits)
- Reasonable management scope
- ThingsBoard relation query optimization

---

## Testing Workflow

1. **Create Scenario** → Define JSON config file
2. **Provision** → Run `provision-scenario.py`
3. **Verify** → Check ThingsBoard UI (Assets, Devices, Relations)
4. **Configure Gateway** → Update `.env.ebmpapst-gateway` with gateway token
5. **Run Test** → Execute `./start-ebmpapst-gateway.sh`
6. **Create Dashboard** → Use ThingsBoard UI with provisioned entities
7. **Monitor** → Observe telemetry, test queries, check performance

---

**Last Updated:** 2025-10-17
