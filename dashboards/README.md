# Dashboard Files

## Important Notice

**Dashboards should be created manually via the ThingsBoard UI.**

Automated dashboard creation via scripts has been **deprecated** due to:
- Complex widget configuration requirements
- ThingsBoard JSON format inconsistencies
- Widget initialization errors
- Difficult to maintain and troubleshoot

---

## Available Files

### Working Reference Template

**`cleanroom_working.json`**
- Basic table view dashboard showing all 60 FFU devices
- Can be used as a reference when creating dashboards manually in ThingsBoard UI
- Shows correct widget configuration structure

### Archived Files

**`archive/`** directory contains:
- `cleanroom_hierarchical.json` - Multi-state navigation attempt (widget errors)
- `cleanroom_hierarchical_simple.json` - Relations query attempt (subscription errors)
- `cleanroom_hierarchical_v2.json` - Entity list attempt (partial success but complex)

These are kept for historical reference only and are **not recommended for use**.

---

## Recommended Approach

### Option A: Flat View Dashboard

1. Login to ThingsBoard UI
2. Go to Dashboards → Add new dashboard
3. Add "Entities Table" widget
4. Configure entity alias to show all FFU devices (DW00000000-DW00000059)
5. Add data keys: actualSpeed, speedSetpoint, differentialPressure, motorTemperature, powerConsumption, operatingHours
6. Enable: displayEntityName, enableSearch, displayPagination

### Option B: Hierarchical Dashboard

1. Create dashboard with multiple states or sections
2. Use asset hierarchy:
   - Building A
   - Floor 5
     - Room R501 (ISO 5) - Devices DW00000000-029
     - Room R502 (ISO 6) - Devices DW00000030-059
3. Add navigation widgets between states
4. Filter devices by room using entity name patterns or relations

---

## Asset Hierarchy

The asset hierarchy has been created and is available:

```
Building A (0ed3f8e0-ab33-11f0-af4d-97d7c19de825)
└─ Floor 5 (0ef3dcf0-ab33-11f0-af4d-97d7c19de825)
    ├─ Room R501 (0f279720-ab33-11f0-af4d-97d7c19de825) - ISO 5
    │   └─ 30 FFU devices (DW00000000-DW00000029)
    └─ Room R502 (0f597c90-ab33-11f0-af4d-97d7c19de825) - ISO 6
        └─ 30 FFU devices (DW00000030-DW00000059)
```

Use these asset IDs and relations when creating hierarchical dashboards in the UI.

---

## Why Manual Creation?

ThingsBoard's dashboard JSON format is:
- **Complex**: Deeply nested configuration with strict requirements
- **Version-dependent**: Different ThingsBoard versions may have different widget formats
- **Widget-specific**: Each widget type has unique configuration structure
- **Error-prone**: Small mistakes cause JavaScript errors in browser
- **Hard to debug**: Errors only appear when dashboard loads in UI

The ThingsBoard UI provides:
- Visual widget configuration
- Real-time validation
- Drag-and-drop layout
- Built-in widget templates
- Immediate error feedback

---

**Recommendation**: Use the UI for all dashboard creation and management.
