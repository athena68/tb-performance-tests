# Cleanroom FFU Monitoring Dashboard - Implementation Plan

**Project Goal:** Create a hierarchical cleanroom monitoring dashboard similar to ThingsBoard Smart Retail demo, starting simple and evolving to complex multi-level navigation.

**Current Setup:**
- 60 FFU devices (DW00000000 - DW00000059)
- 1 Gateway (GW00000000)
- ThingsBoard CE server at http://167.99.64.71:8080

**Target Structure:**
```
Building A (Hanoi Cleanroom Facility)
└─ Floor 5
    ├─ Room R501 (ISO 5 Cleanroom) → 30 FFUs (DW00000000-DW00000029)
    └─ Room R502 (ISO 6 Cleanroom) → 30 FFUs (DW00000030-DW00000059)
```

---

## Phase 1: Option A - Simple Flat Dashboard (Foundation)

**Goal:** Single-page dashboard showing all 60 FFUs with basic grouping and monitoring

**Estimated Time:** 2-3 hours
**Complexity:** ⭐ Easy
**Upgrade Path:** ✅ Fully compatible with Phase 2

### 1.1 Entity Setup (No hierarchy yet)

**Step 1.1.1: Verify Existing Entities**
```bash
# Script: verify-current-setup.sh
# - List all 60 FFU devices (DW00000000-DW00000059)
# - Verify gateway GW00000000
# - Check device profile EBMPAPST_FFU
# - Verify telemetry data is flowing
```

**Deliverable:** `verify-current-setup.sh` script
**Test:** Run script, confirm 60 devices exist and have telemetry data

---

### 1.2 Dashboard Design - Single State

**Widget Layout:**
```
+------------------------+------------------------+------------------------+------------------------+
|   Card Widget          |   Card Widget          |   Card Widget          |   Card Widget          |
|   Total FFUs: 60       |   Active: 58           |   Alarms: 2            |   Avg Speed: 1547 RPM  |
+------------------------+------------------------+------------------------+------------------------+
|                                                                                                   |
|   Entities Table Widget                                                                           |
|   - All 60 FFUs with real-time telemetry (Speed, Pressure, Temperature, Status)                  |
|   - Sortable columns                                                                              |
|   - Color-coded status                                                                            |
|   - Click row → Navigate to device details state                                                  |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   Time Series Chart Widget (Speed)                      |   Time Series Chart Widget (Pressure)   |
|   - Show aggregated speed from all FFUs                 |   - Show aggregated differential pressure|
|   - Last 1 hour (configurable)                          |   - Threshold line at 450 Pa             |
|                                                                                                   |
+--------------------------------------------------+----------------------------------------------------+
|                                                                                                   |
|   Alarms Table Widget                                                                             |
|   - Active alarms from all FFUs                                                                   |
|   - Severity-based filtering                                                                      |
|   - Acknowledge/Clear actions                                                                     |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

**ThingsBoard Components Used:**
- **Widget Library:**
  - `cards` bundle → `simple_card` (for metrics cards)
  - `tables` bundle → `entities_table` (for FFU list)
  - `charts` bundle → `timeseries_chart` (for trends)
  - `alarm_widgets` bundle → `alarms_table` (for alarms)

**Entity Alias Configuration:**
```javascript
// Alias: "All FFU Devices"
{
  "id": "all_ffu_devices",
  "alias": "All FFU Devices",
  "filter": {
    "type": "deviceType",
    "deviceTypes": ["EBMPAPST_FFU"],
    "resolveMultiple": true
  }
}
```

**Deliverable:**
- `cleanroom_dashboard_v1_flat.json` (Dashboard JSON)
- `create-dashboard-v1.sh` (Script to import dashboard)

**Test Checklist:**
- [ ] All 60 FFUs appear in table
- [ ] Real-time telemetry updates (speed, pressure, temperature)
- [ ] Cards show correct aggregated values
- [ ] Charts display historical data
- [ ] Alarms table shows active alarms
- [ ] Click FFU row → Navigate to device state

---

### 1.3 Device Details State (Drill-down)

**State Name:** `device_details`
**State Parameters:** `${entityId}`, `${entityName}`

**Widget Layout:**
```
+------------------------+------------------------+------------------------+------------------------+
|   Card: Current Speed  |   Card: Pressure       |   Card: Temperature    |   Card: Power          |
+------------------------+------------------------+------------------------+------------------------+
|                                                                                                   |
|   Time Series Chart: Speed History (actualSpeed vs speedSetpoint)                                |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   Time Series Chart: Differential Pressure History (with 450 Pa threshold)                       |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
|   Time Series Chart: Temperature   |   Time Series Chart: Power Consumption                      |
+------------------------------------+-------------------------------------------------------------+
|                                                                                                   |
|   Attributes Table: Device metadata (fanModel, manufacturer, serialNumber, etc.)                  |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   Alarms Table: Device-specific alarm history                                                     |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

**Entity Alias Configuration:**
```javascript
// Alias: "Current Device"
{
  "id": "current_device",
  "alias": "Current Device",
  "filter": {
    "type": "entityList",
    "entityType": "DEVICE",
    "entityList": ["${entityId}"],
    "resolveMultiple": false
  }
}
```

**Navigation Action:**
```javascript
// From entities table to device state
{
  "id": "navigate_to_device",
  "name": "Show device details",
  "icon": "info",
  "type": "openDashboardState",
  "targetDashboardStateId": "device_details",
  "setEntityIdInState": true
}
```

**Deliverable:** Updated `cleanroom_dashboard_v1_flat.json` with device state

**Test Checklist:**
- [ ] Click any FFU in table → Navigate to device details
- [ ] Device name shows in breadcrumb
- [ ] All telemetry cards display current values
- [ ] Historical charts show 24-hour data
- [ ] Attributes table shows all 42 attributes
- [ ] Device-specific alarms appear

---

## Phase 2: Option B - Hierarchical Dashboard (Advanced)

**Goal:** Multi-level navigation with Assets (Building → Floor → Room) and visual hierarchy

**Estimated Time:** 4-6 hours
**Complexity:** ⭐⭐⭐ Advanced
**Prerequisites:** Phase 1 completed and tested

### 2.1 Entity Hierarchy Setup

**Step 2.1.1: Create Asset Structure**

**Script:** `create-cleanroom-assets.sh`

**Assets to Create:**

1. **Building Asset:**
```json
{
  "name": "Building A - Hanoi Cleanroom",
  "type": "Building",
  "label": "Hanoi Facility",
  "additionalInfo": {
    "description": "Semiconductor cleanroom facility",
    "location": "Hanoi, Vietnam",
    "latitude": 21.0285,
    "longitude": 105.8542,
    "address": "Duy Tan Street, Cau Giay District, Hanoi",
    "totalFloors": 1,
    "operationalSince": "2023-01-15"
  }
}
```

2. **Floor Asset:**
```json
{
  "name": "Floor 5",
  "type": "Floor",
  "label": "Level 5 - Cleanroom Area",
  "additionalInfo": {
    "description": "ISO 5-6 classified cleanroom zone",
    "floorNumber": 5,
    "totalRooms": 2,
    "totalArea": "500 sqm"
  }
}
```

3. **Room Assets:**
```json
[
  {
    "name": "Room R501",
    "type": "Room",
    "label": "ISO 5 Cleanroom - Wafer Processing",
    "additionalInfo": {
      "description": "Ultra-clean zone for wafer processing",
      "isoClass": "ISO 5",
      "area": "250 sqm",
      "ffuCount": 30,
      "targetPressure": 250,
      "targetTemperature": 22,
      "targetHumidity": 45
    }

  {
    "name": "Room R502",
    "type": "Room",
    "label": "ISO 6 Cleanroom - Assembly",
    "additionalInfo": {
      "description": "Clean zone for component assembly",
      "isoClass": "ISO 6",
      "area": "250 sqm",
      "ffuCount": 30,
      "targetPressure": 200,
      "targetTemperature": 23,
      "targetHumidity": 50
    }
  }
]
```

**Deliverable:** `create-cleanroom-assets.sh` script

**Test Checklist:**
- [ ] Building A asset created
- [ ] Floor 5 asset created
- [ ] Room R501 and R502 assets created
- [ ] Attributes populated correctly

---

**Step 2.1.2: Establish Entity Relations**

**Script:** `create-cleanroom-relations.sh`

**Relations to Create:**

```
Building A --[Contains]--> Floor 5
Floor 5 --[Contains]--> Room R501
Floor 5 --[Contains]--> Room R502
Room R501 --[Contains]--> Gateway GW00000000
Gateway GW00000000 --[Contains]--> FFU DW00000000-DW00000029 (30 devices)
Room R502 --[Manages]--> FFU DW00000030-DW00000059 (30 devices)
```

**Relation Types:**
- `Contains`: Hierarchical ownership (Building → Floor → Room → Gateway → Devices)
- `Manages`: Room manages FFUs (for filtering and grouping)

**Implementation:**
```bash
# Create "Contains" relation: Building A → Floor 5
curl -X POST "http://167.99.64.71:8080/api/relation" \
  -H "X-Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from": {"id": "'$BUILDING_ID'", "entityType": "ASSET"},
    "to": {"id": "'$FLOOR_ID'", "entityType": "ASSET"},
    "type": "Contains",
    "typeGroup": "COMMON"
  }'

# Similar for Floor → Rooms, Room → Gateway, Gateway → FFUs
```

**Deliverable:** `create-cleanroom-relations.sh` script

**Test Checklist:**
- [ ] Building A contains Floor 5 (check Relations tab)
- [ ] Floor 5 contains Room R501 and R502
- [ ] Room R501 contains/manages 30 FFUs (DW00000000-DW00000029)
- [ ] Room R502 manages 30 FFUs (DW00000030-DW00000059)
- [ ] Gateway GW00000000 properly linked

---

### 2.2 Hierarchical Dashboard States

**Dashboard States:**

1. **State: `default`** (Facility Overview)
2. **State: `building`** (Building A View)
3. **State: `floor`** (Floor 5 View)
4. **State: `room`** (Room R501/R502 View)
5. **State: `device`** (Individual FFU View)

---

**State 1: Facility Overview (default)**

**Entity Alias:**
```javascript
{
  "id": "facility",
  "alias": "Facility",
  "filter": {
    "type": "assetType",
    "assetTypes": ["Building"],
    "resolveMultiple": false
  }
}
```

**Widget Layout:**
```
+------------------------+------------------------+------------------------+------------------------+
|   Card: Buildings      |   Card: Total Rooms    |   Card: Total FFUs     |   Card: Active Alarms  |
|   Value: 1             |   Value: 2             |   Value: 60            |   Value: 2             |
+------------------------+------------------------+------------------------+------------------------+
|                                                  |                                                  |
|   Entity Hierarchy Widget (Tree View)           |   Summary Cards Grid                             |
|   - Building A                                   |   - Building A: 60 FFUs, 2 alarms               |
|     - Floor 5                                    |   - Avg Speed: 1547 RPM                          |
|       - Room R501 (30 FFUs)                      |   - Avg Pressure: 287 Pa                         |
|       - Room R502 (30 FFUs)                      |   - Status: Normal                               |
|                                                  |                                                  |
|   (Click to navigate to each level)             |                                                  |
+--------------------------------------------------+--------------------------------------------------+
|                                                                                                   |
|   Alarms Table Widget (All facility alarms)                                                      |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

**Navigation Widget (Custom HTML/TBEL):**
```html
<!-- Hierarchical Tree Navigation -->
<div class="hierarchy-tree">
  <ul>
    <li onclick="navigateTo('building', buildingId)">
      <i class="material-icons">business</i> Building A
      <ul>
        <li onclick="navigateTo('floor', floorId)">
          <i class="material-icons">layers</i> Floor 5
          <ul>
            <li onclick="navigateTo('room', room501Id)">
              <i class="material-icons">meeting_room</i> Room R501 (30 FFUs)
            </li>
            <li onclick="navigateTo('room', room502Id)">
              <i class="material-icons">meeting_room</i> Room R502 (30 FFUs)
            </li>
          </ul>
        </li>
      </ul>
    </li>
  </ul>
</div>

<script>
function navigateTo(state, entityId) {
  // ThingsBoard API to navigate to state
  tbApi.openDashboardState(state, { entityId: entityId });
}
</script>

<style>
.hierarchy-tree ul { list-style: none; padding-left: 20px; }
.hierarchy-tree li { cursor: pointer; padding: 8px; }
.hierarchy-tree li:hover { background: #e3f2fd; }
.hierarchy-tree i { vertical-align: middle; margin-right: 8px; }
</style>
```

**Deliverable:** State configuration in dashboard JSON

**Test Checklist:**
- [ ] Facility overview loads by default
- [ ] Cards show correct totals
- [ ] Tree navigation widget displays hierarchy
- [ ] Click Building A → Navigate to building state
- [ ] Click Room R501 → Navigate to room state

---

**State 2: Building View**

**Entity Alias:**
```javascript
{
  "id": "current_building",
  "alias": "Current Building",
  "filter": {
    "type": "entityList",
    "entityType": "ASSET",
    "entityList": ["${entityId}"],
    "resolveMultiple": false
  }
}

{
  "id": "building_floors",
  "alias": "Floors in Building",
  "filter": {
    "type": "relationsQuery",
    "rootEntity": {
      "entityType": "ASSET",
      "id": "${entityId}"
  
    "direction": "FROM",
    "relationType": "Contains",
    "filters": [
      {
        "key": "type",
        "valueType": "STRING",
        "value": "Floor"
      }
    ],
    "resolveMultiple": true
  }
}
```

**Widget Layout:**
```
+------------------------+------------------------+------------------------+------------------------+
| Breadcrumb: Facility > Building A                                                                |
+------------------------+------------------------+------------------------+------------------------+
|   Card: Total Floors   |   Card: Total Rooms    |   Card: Total FFUs     |   Card: Avg Pressure   |
|   Value: 1             |   Value: 2             |   Value: 60            |   Value: 287 Pa        |
+------------------------+------------------------+------------------------+------------------------+
|                                                  |                                                  |
|   Floors Table Widget                            |   Building Summary Chart                         |
|   - Floor 5 (2 rooms, 60 FFUs)                   |   - Aggregated pressure trends                   |
|   - Click row → Navigate to floor state          |   - Last 24 hours                                |
|                                                  |                                                  |
+--------------------------------------------------+--------------------------------------------------+
|                                                                                                   |
|   Rooms Table Widget (All rooms in building)                                                     |
|   - Room R501: 30 FFUs, ISO 5, Status: Normal                                                    |
|   - Room R502: 30 FFUs, ISO 6, Status: Normal                                                    |
|   - Click row → Navigate to room state                                                           |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

**Navigation Actions:**
```javascript
// Table row click → Navigate to floor state
{
  "type": "openDashboardState",
  "targetDashboardStateId": "floor",
  "setEntityIdInState": true
}
```

**Deliverable:** Building state configuration

**Test Checklist:**
- [ ] Breadcrumb shows "Facility > Building A"
- [ ] Cards show building-specific metrics
- [ ] Floors table lists Floor 5
- [ ] Rooms table lists R501 and R502
- [ ] Click Floor 5 → Navigate to floor state
- [ ] Click Room R501 → Navigate to room state

---

**State 3: Floor View**

**Entity Alias:**
```javascript
{
  "id": "current_floor",
  "alias": "Current Floor",
  "filter": {
    "type": "entityList",
    "entityType": "ASSET",
    "entityList": ["${entityId}"]
  }
}

{
  "id": "floor_rooms",
  "alias": "Rooms on Floor",
  "filter": {
    "type": "relationsQuery",
    "rootEntity": { "entityType": "ASSET", "id": "${entityId}" },
    "direction": "FROM",
    "relationType": "Contains",
    "filters": [{ "key": "type", "valueType": "STRING", "value": "Room" }],
    "resolveMultiple": true
  }
}

{
  "id": "floor_ffus",
  "alias": "All FFUs on Floor",
  "filter": {
    "type": "relationsQuery",
    "rootEntity": { "entityType": "ASSET", "id": "${entityId}" },
    "direction": "FROM",
    "relationType": "Contains",
    "maxLevel": 3,  // Floor → Room → Gateway → Device
    "filters": [{ "key": "type", "valueType": "STRING", "value": "EBMPAPST_FFU" }],
    "resolveMultiple": true
  }
}
```

**Widget Layout:**
```
+------------------------+------------------------+------------------------+------------------------+
| Breadcrumb: Facility > Building A > Floor 5                                                      |
+------------------------+------------------------+------------------------+------------------------+
|   Card: Total Rooms    |   Card: Total FFUs     |   Card: Avg Speed      |   Card: Avg Temp       |
|   Value: 2             |   Value: 60            |   Value: 1547 RPM      |   Value: 52°C          |
+------------------------+------------------------+------------------------+------------------------+
|                                                                                                   |
|   Floor Plan Image Map Widget (Optional - can use placeholder image)                             |
|   - Show room layout visually                                                                    |
|   - Markers for each room (R501, R502)                                                           |
|   - Color-coded by status (green=normal, red=alarm)                                              |
|   - Click marker → Navigate to room state                                                        |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   Rooms Table Widget                                                                              |
|   - Room R501: 30 FFUs, Avg Pressure: 287 Pa, Status: Normal                                     |
|   - Room R502: 30 FFUs, Avg Pressure: 245 Pa, Status: Normal                                     |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   Time Series Chart: Floor-level aggregated metrics (Speed, Pressure, Temperature)               |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

**Deliverable:** Floor state configuration

**Test Checklist:**
- [ ] Breadcrumb shows "Facility > Building A > Floor 5"
- [ ] Cards show floor-specific aggregated values
- [ ] Rooms table lists R501 and R502 with stats
- [ ] Floor plan (if implemented) shows room markers
- [ ] Aggregated charts display all 60 FFUs data
- [ ] Click room → Navigate to room state

---

**State 4: Room View**

**Entity Alias:**
```javascript
{
  "id": "current_room",
  "alias": "Current Room",
  "filter": {
    "type": "entityList",
    "entityType": "ASSET",
    "entityList": ["${entityId}"]
  }
}

{
  "id": "room_ffus",
  "alias": "FFUs in Room",
  "filter": {
    "type": "relationsQuery",
    "rootEntity": { "entityType": "ASSET", "id": "${entityId}" },
    "direction": "FROM",
    "relationType": "Manages",  // or "Contains" via Gateway
    "maxLevel": 2,
    "filters": [{ "key": "type", "valueType": "STRING", "value": "EBMPAPST_FFU" }],
    "resolveMultiple": true
  }
}
```

**Widget Layout:**
```
+------------------------+------------------------+------------------------+------------------------+
| Breadcrumb: Facility > Building A > Floor 5 > Room R501                                          |
+------------------------+------------------------+------------------------+------------------------+
|   Card: FFU Count      |   Card: Avg Speed      |   Card: Diff Pressure  |   Card: Avg Temp       |
|   Value: 30            |   Value: 1547 RPM      |   Value: 287 Pa        |   Value: 52°C          |
+------------------------+------------------------+------------------------+------------------------+
|   Card: ISO Class      |   Card: Active Alarms  |   Card: Room Status    |   Card: Gateway Status |
|   Value: ISO 5         |   Value: 1             |   Value: Normal        |   Value: Online        |
+------------------------+------------------------+------------------------+------------------------+
|                                                                                                   |
|   FFU Devices Table (All 30 FFUs in this room)                                                   |
|   - Columns: Name, Speed, Pressure, Temperature, Power, Status                                   |
|   - Sortable, filterable                                                                         |
|   - Click row → Navigate to device state                                                         |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
|                                                  |                                                  |
|   Time Series Chart: Room Speed Trend           |   Time Series Chart: Room Pressure Trend         |
|                                                  |                                                  |
+--------------------------------------------------+--------------------------------------------------+
|                                                  |                                                  |
|   Time Series Chart: Room Temperature           |   Alarms Table: Room-specific alarms             |
|                                                  |                                                  |
+--------------------------------------------------+--------------------------------------------------+
```

**Deliverable:** Room state configuration

**Test Checklist:**
- [ ] Breadcrumb shows full path to room
- [ ] Cards show room-specific values (30 FFUs)
- [ ] FFU table lists exactly 30 devices (DW00000000-029 for R501, 030-059 for R502)
- [ ] Charts show aggregated data from room FFUs only
- [ ] Click FFU row → Navigate to device state
- [ ] Gateway status card shows GW00000000 online

---

**State 5: Device View** (Already implemented in Phase 1, reuse)

**No changes needed** - Same as Phase 1 device details state

---

### 2.3 Navigation Sidebar Widget (Custom)

**Implementation:** Use ThingsBoard's HTML Card widget with custom TBEL script

**Widget Type:** `HTML Card` (from `cards` bundle)

**TBEL Script:**
```javascript
// Fetch entity hierarchy using relations API
var buildingId = 'xxx';  // Replace with actual Building A ID
var floorId = 'yyy';     // Replace with actual Floor 5 ID
var room501Id = 'zzz';   // Replace with actual Room R501 ID
var room502Id = 'aaa';   // Replace with actual Room R502 ID

// Generate HTML tree structure
var html = `
<div class="nav-sidebar">
  <div class="nav-header">Navigation</div>
  <ul class="nav-tree">
    <li>
      <div class="nav-item" onclick="navigateToEntity('default', null)">
        <i class="material-icons">home</i>
        <span>Facility Overview</span>
      </div>
    </li>
    <li>
      <div class="nav-item" onclick="navigateToEntity('building', '${buildingId}')">
        <i class="material-icons">business</i>
        <span>Building A</span>
      </div>
      <ul>
        <li>
          <div class="nav-item" onclick="navigateToEntity('floor', '${floorId}')">
            <i class="material-icons">layers</i>
            <span>Floor 5</span>
          </div>
          <ul>
            <li>
              <div class="nav-item" onclick="navigateToEntity('room', '${room501Id}')">
                <i class="material-icons">meeting_room</i>
                <span>Room R501 (30 FFUs)</span>
              </div>
            </li>
            <li>
              <div class="nav-item" onclick="navigateToEntity('room', '${room502Id}')">
                <i class="material-icons">meeting_room</i>
                <span>Room R502 (30 FFUs)</span>
              </div>
            </li>
          </ul>
        </li>
      </ul>
    </li>
  </ul>
</div>

<style>
.nav-sidebar {
  background: #ffffff;
  border-right: 1px solid #e0e0e0;
  height: 100%;
  padding: 16px;
  overflow-y: auto;
}
.nav-header {
  font-size: 18px;
  font-weight: 600;
  color: #305680;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #305680;
}
.nav-tree {
  list-style: none;
  padding: 0;
  margin: 0;
}
.nav-tree ul {
  list-style: none;
  padding-left: 20px;
  margin-top: 4px;
}
.nav-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}
.nav-item:hover {
  background: #e3f2fd;
}
.nav-item i {
  margin-right: 12px;
  color: #305680;
  font-size: 20px;
}
.nav-item span {
  font-size: 14px;
  color: #333333;
}
.nav-item.active {
  background: #1976d2;
  color: #ffffff;
}
.nav-item.active i,
.nav-item.active span {
  color: #ffffff;
}
</style>

<script>
function navigateToEntity(state, entityId) {
  if (entityId) {
    tbApi.openDashboardState(state, { entityId: entityId });
  } else {
    tbApi.openDashboardState(state);
  }
}
</script>
`;

return html;
```

**Deliverable:** Custom navigation sidebar widget configuration

**Test Checklist:**
- [ ] Sidebar appears on left side of dashboard
- [ ] Tree structure displays correctly
- [ ] Icons and text properly styled
- [ ] Click Facility → Navigate to default state
- [ ] Click Building A → Navigate to building state
- [ ] Click Floor 5 → Navigate to floor state
- [ ] Click Room R501 → Navigate to room state
- [ ] Active state highlighted in sidebar

---

## Phase 3: Testing and Validation

### 3.1 Automated Testing Script

**Script:** `test-cleanroom-dashboard.sh`

**Tests to Perform:**

1. **Entity Validation:**
   - [ ] Verify Building A exists
   - [ ] Verify Floor 5 exists
   - [ ] Verify Room R501 and R502 exist
   - [ ] Verify all 60 FFUs exist

2. **Relations Validation:**
   - [ ] Building A contains Floor 5
   - [ ] Floor 5 contains Room R501 and R502
   - [ ] Room R501 manages 30 FFUs (DW00000000-029)
   - [ ] Room R502 manages 30 FFUs (DW00000030-059)
   - [ ] Gateway GW00000000 contains all 60 FFUs

3. **Dashboard Validation:**
   - [ ] Dashboard imported successfully
   - [ ] All states defined (default, building, floor, room, device)
   - [ ] Entity aliases resolve correctly
   - [ ] Widgets load without errors

4. **Data Flow Validation:**
   - [ ] Telemetry data flowing from all 60 FFUs
   - [ ] Attributes populated for all devices
   - [ ] Alarms triggering and clearing correctly

**Deliverable:** `test-cleanroom-dashboard.sh` script with automated checks

---

### 3.2 Manual Testing Checklist

**User Acceptance Testing:**

**Scenario 1: Facility Overview**
- [ ] Load dashboard → Default state shows facility overview
- [ ] Total FFUs card shows 60
- [ ] Active alarms card shows correct count
- [ ] Sidebar navigation displays hierarchy
- [ ] Alarms table shows all active alarms

**Scenario 2: Navigate to Building**
- [ ] Click "Building A" in sidebar → Building state loads
- [ ] Breadcrumb shows "Facility > Building A"
- [ ] Building metrics display correctly
- [ ] Rooms table lists R501 and R502

**Scenario 3: Navigate to Floor**
- [ ] Click "Floor 5" in sidebar → Floor state loads
- [ ] Breadcrumb shows "Facility > Building A > Floor 5"
- [ ] Floor metrics aggregate all 60 FFUs
- [ ] Rooms table shows 2 rooms with stats

**Scenario 4: Navigate to Room**
- [ ] Click "Room R501" in sidebar → Room state loads
- [ ] Breadcrumb shows full path to room
- [ ] FFU count card shows 30
- [ ] FFU table lists exactly 30 devices (DW00000000-029)
- [ ] Charts show room-specific data

**Scenario 5: Navigate to Device**
- [ ] Click any FFU row in room table → Device state loads
- [ ] Device name shows in breadcrumb
- [ ] All telemetry cards display current values
- [ ] Historical charts show device-specific data
- [ ] Attributes table shows all 42 attributes

**Scenario 6: Back Navigation**
- [ ] Click breadcrumb "Room R501" → Return to room state
- [ ] Click breadcrumb "Floor 5" → Return to floor state
- [ ] Click breadcrumb "Building A" → Return to building state
- [ ] Click breadcrumb "Facility" → Return to overview

**Scenario 7: Sidebar Navigation**
- [ ] Click different rooms in sidebar → States switch correctly
- [ ] Active state highlighted in sidebar
- [ ] All navigation paths work consistently

---

## Phase 4: Documentation and Deployment

### 4.1 Deployment Scripts

**Master Deployment Script:** `deploy-cleanroom-dashboard.sh`

```bash
#!/bin/bash
# Master deployment script for cleanroom dashboard

echo "=========================================="
echo "Cleanroom Dashboard Deployment"
echo "=========================================="

# Phase 1: Verify environment
echo "Phase 1: Verifying environment..."
./verify-current-setup.sh || exit 1

# Phase 2: Create assets (Option B only)
if [ "$DEPLOY_OPTION_B" = "true" ]; then
  echo "Phase 2: Creating asset hierarchy..."
  ./create-cleanroom-assets.sh || exit 1

  echo "Phase 3: Establishing relations..."
  ./create-cleanroom-relations.sh || exit 1
fi

# Phase 4: Deploy dashboard
echo "Phase 4: Deploying dashboard..."
if [ "$DEPLOY_OPTION_B" = "true" ]; then
  ./create-dashboard-v2-hierarchical.sh || exit 1
else
  ./create-dashboard-v1-flat.sh || exit 1
fi

# Phase 5: Run tests
echo "Phase 5: Running validation tests..."
./test-cleanroom-dashboard.sh || exit 1

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Dashboard URL: http://167.99.64.71:8080/dashboard/<DASHBOARD_ID>"
echo ""
```

**Environment Variables:**
```bash
# .env.cleanroom-dashboard
REST_URL=http://167.99.64.71:8080
REST_USERNAME=tenant@thingsboard.org
REST_PASSWORD=tenant

# Deployment options
DEPLOY_OPTION_B=false  # Set to true for hierarchical dashboard

# Entity IDs (populated after creation)
BUILDING_A_ID=
FLOOR_5_ID=
ROOM_R501_ID=
ROOM_R502_ID=
GATEWAY_ID=

# Dashboard settings
DASHBOARD_DELETE_IF_EXISTS=true
```

**Deliverable:** Complete deployment package with all scripts

---

### 4.2 User Guide

**Document:** `CLEANROOM_DASHBOARD_USER_GUIDE.md`

**Contents:**
1. Dashboard Overview
2. Navigation Guide (Sidebar, Breadcrumbs, Tables)
3. Widget Descriptions (Cards, Charts, Tables)
4. Alarm Management
5. Troubleshooting

**Deliverable:** User guide markdown document

---

### 4.3 ThingsBoard Best Practices Applied

**Reference Documentation:**
- [ThingsBoard Dashboard Development Guide](https://thingsboard.io/docs/user-guide/dashboards/)
- [ThingsBoard Entity Relations](https://thingsboard.io/docs/user-guide/entities-and-relations/)
- [Widget Development with TBEL](https://thingsboard.io/docs/user-guide/contribution/widgets-development/)

**Best Practices Implemented:**

1. **Entity Modeling:**
   - ✅ Use Assets for hierarchical structure (Building, Floor, Room)
   - ✅ Use Devices for sensors (FFUs)
   - ✅ Establish proper relations (Contains, Manages)

2. **Dashboard Design:**
   - ✅ Use states for multi-level navigation
   - ✅ Entity aliases for dynamic data binding
   - ✅ State parameters for context passing
   - ✅ Navigation actions for drill-down

3. **Widget Configuration:**
   - ✅ Use built-in widgets from ThingsBoard library
   - ✅ TBEL for dynamic calculations
   - ✅ JavaScript for custom interactions
   - ✅ Responsive layout with grid system

4. **Performance:**
   - ✅ Efficient entity aliases (avoid deep relation queries)
   - ✅ Aggregation for large datasets
   - ✅ Limit time windows for charts
   - ✅ Pagination for tables

---

## Upgrade Path: Option A → Option B

**Incremental Upgrade Steps:**

### Step 1: Keep Option A Running
- Option A dashboard remains functional during upgrade
- No downtime required

### Step 2: Create Assets (Non-disruptive)
- Run `create-cleanroom-assets.sh`
- Creates Building, Floor, Room assets
- Does not affect existing devices or dashboard

### Step 3: Establish Relations (Non-disruptive)
- Run `create-cleanroom-relations.sh`
- Links assets to existing devices
- Does not modify device data or telemetry

### Step 4: Deploy Option B Dashboard
- Run `create-dashboard-v2-hierarchical.sh`
- Creates new dashboard (parallel to Option A)
- Validates functionality

### Step 5: Compare and Switch
- Test both dashboards side-by-side
- Verify Option B has all Option A features plus hierarchy
- Delete Option A dashboard when satisfied
- Set Option B as default

**Rollback Plan:**
- Keep Option A dashboard ID
- If issues with Option B, delete it and revert to Option A
- No data loss, only dashboard configuration changes

---

## Timeline and Effort Estimates

### Option A (Simple Flat Dashboard)
- **Setup and Verify:** 30 minutes
- **Dashboard Design:** 1 hour
- **Device State Implementation:** 1 hour
- **Testing:** 30 minutes
- **Total:** 3 hours

### Option B (Hierarchical Dashboard)
- **Asset Creation:** 1 hour
- **Relations Establishment:** 1 hour
- **Dashboard States (5 states):** 2 hours
- **Navigation Sidebar:** 1 hour
- **Testing:** 1 hour
- **Total:** 6 hours

### Upgrade Path (A → B)
- **Incremental upgrade:** 4 hours (parallel deployment + testing)

---

## Deliverables Summary

### Phase 1 (Option A):
1. ✅ `verify-current-setup.sh`
2. ✅ `cleanroom_dashboard_v1_flat.json`
3. ✅ `create-dashboard-v1.sh`
4. ✅ `test-dashboard-v1.sh`

### Phase 2 (Option B):
1. ✅ `create-cleanroom-assets.sh`
2. ✅ `create-cleanroom-relations.sh`
3. ✅ `cleanroom_dashboard_v2_hierarchical.json`
4. ✅ `create-dashboard-v2-hierarchical.sh`
5. ✅ `test-cleanroom-dashboard.sh`

### Phase 3 (Documentation):
1. ✅ `CLEANROOM_DASHBOARD_USER_GUIDE.md`
2. ✅ `deploy-cleanroom-dashboard.sh`
3. ✅ `.env.cleanroom-dashboard`

---

## Next Steps

**Immediate Actions:**

1. **Review this plan** - Confirm approach aligns with requirements
2. **Start with Phase 1 (Option A)** - Build foundation first
3. **Test Option A thoroughly** - Validate all features work
4. **Proceed to Phase 2 (Option B)** - Add hierarchical navigation
5. **Deploy and train users** - Provide user guide and support

**Questions for Approval:**

1. ✅ Confirm 30 FFUs per room (2 rooms total)
2. ✅ Confirm entity structure: Building A → Floor 5 → Room R501/R502
3. ✅ Confirm starting with 1 building only
4. ✅ Approve phased approach (A then B)

**Ready to start implementation?** 🚀
