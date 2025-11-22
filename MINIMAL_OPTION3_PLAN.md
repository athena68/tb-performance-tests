# Minimal Option 3 Implementation Plan

## Core Focus
- **Python:** Assets ONLY + .env generation
- **Java:** Devices/Gateways ONLY + asset discovery
- **Goal:** Test separation approach ASAP

## Implementation (2-3 hours max)

### Phase 1: Python Asset Script (1 hour)
**NEW:** `test-scenarios/asset-provision.py`
- ✅ Load JSON scenario (reuse existing format)
- ✅ Create Site → Building → Floor → Room (reuse existing logic)
- ❌ **NO device/gateway creation**
- ✅ Generate .env with room assignments
- ✅ Basic error handling

### Phase 2: Java Asset Discovery (1 hour)
**MODIFY:** Existing Java classes
- ✅ Add AssetDiscoveryService (minimal)
- ✅ Update BaseTestExecutor to detect hierarchy
- ✅ Enhance AbstractAPITest with smart device allocation
- ✅ Basic room-to-device linking

### Phase 3: Template & Testing (1 hour)
**NEW:** `.env.example` template
**VERIFY:** End-to-end workflow

## Quick Test Scenario
```bash
# Step 1: Create assets only
python test-scenarios/asset-provision.py scenarios/cleanroom.json

# Step 2: Test Java device creation with generated .env
source .env
mvn spring-boot:run
```

**Success Criteria:**
- ✅ No device conflicts
- ✅ Devices linked to correct rooms
- ✅ Java app detects Python hierarchy