# Refactoring Plan: Hybrid Coordination (Option 3)

## Executive Summary

This refactoring adds minimal coordination between the existing Java and Python entity creation systems while keeping both systems largely unchanged. The approach preserves existing functionality and investments while adding conflict detection, entity discovery, and better user guidance. This is a low-risk, quick-win solution that can be implemented in 2-3 weeks.

## Current Architecture (What We're Keeping)

### **Python System** (Unchanged)
- ✅ Creates hierarchical assets (Site → Building → Floor → Room)
- ✅ Creates gateways and devices within hierarchy
- ✅ Establishes relations between entities
- ✅ Uses JSON scenario configuration
- **Location:** `test-scenarios/provision-scenario.py`

### **Java System** (Unchanged)
- ✅ Creates devices and gateways via environment variables
- ✅ Creates customers and dashboards
- ✅ Manages device profiles and rule chains
- ✅ Handles performance testing execution
- **Location:** `src/main/java/org/thingsboard/tools/service/`

### **What We're Adding**
- 🔧 **Entity Existence Checking** - Java app checks for existing entities before creating
- 🔧 **Conflict Detection** - Warn about duplicate entities
- 🔧 **Entity Discovery** - Find and use existing entities
- 🔧 **Better Logging** - Clear visibility into what each system does
- 🔧 **Naming Convention Standards** - Consistent entity naming

## Problems Being Solved

### **1. User Confusion**
- **Problem:** Users don't know which system to use when
- **Solution:** Clear usage guidelines and detection of existing entities

### **2. Duplicate Entity Creation**
- **Problem:** Both systems can create the same devices/gateways
- **Solution:** Existence checking with skip/warn behavior

### **3. No Coordination**
- **Problem:** Systems operate independently with no awareness
- **Solution:** Basic conflict detection and logging

### **4. Cleanup Complexity**
- **Problem:** Users don't know how to clean up properly
- **Solution:** Better cleanup scripts and guidance

## Minimal Changes Required

### **Change 1: Entity Discovery Service**
**New File:** `src/main/java/org/thingsboard/tools/service/discovery/EntityDiscoveryService.java`

```java
@Service
public class EntityDiscoveryService {

    @Autowired
    private RestClientService restClientService;

    // Simple existence checking methods
    public boolean deviceExists(String deviceName) {
        try {
            Device device = restClientService.getDeviceByName(deviceName);
            return device != null;
        } catch (Exception e) {
            return false;
        }
    }

    public boolean gatewayExists(String gatewayName) {
        return deviceExists(gatewayName); // Gateways are just devices with "Gateway" type
    }

    public boolean assetExists(String assetName) {
        try {
            Asset asset = restClientService.getAssetByName(assetName);
            return asset != null;
        } catch (Exception e) {
            return false;
        }
    }

    // Find existing entities for our test range
    public List<DeviceInfo> findExistingDevices(String prefix, int startIdx, int endIdx) {
        List<DeviceInfo> existingDevices = new ArrayList<>();
        for (int i = startIdx; i <= endIdx; i++) {
            String deviceName = prefix + String.format("%08d", i);
            if (deviceExists(deviceName)) {
                existingDevices.add(new DeviceInfo(deviceName, i));
            }
        }
        return existingDevices;
    }

    // Check for Python-created hierarchy
    public boolean hasHierarchicalAssets() {
        try {
            // Look for typical Python-created asset types
            return assetExists("Site") ||
                   findAssetsByType("Site").size() > 0 ||
                   findAssetsByType("Building").size() > 0;
        } catch (Exception e) {
            return false;
        }
    }

    public List<Asset> findAssetsByType(String type) {
        // Simple implementation - get all assets and filter by type
        List<Asset> allAssets = restClientService.getAllAssets();
        return allAssets.stream()
                .filter(asset -> type.equals(asset.getType()))
                .collect(Collectors.toList());
    }
}
```

### **Change 2: Enhanced DeviceManager**
**Modification to:** `src/main/java/org/thingsboard/tools/service/device/DeviceManager.java`

```java
@Service
public class DeviceManager {

    @Autowired
    private RestClientService restClientService;

    @Autowired
    private EntityDiscoveryService discoveryService;

    // Existing methods remain unchanged...

    // NEW: Enhanced creation with existence checking
    public String createDeviceIfNotExists(String deviceName, String deviceType) {
        if (discoveryService.deviceExists(deviceName)) {
            log.info("Device '{}' already exists, skipping creation", deviceName);
            return null; // Return null to indicate it wasn't created
        }

        log.info("Creating new device: '{}' with type: '{}'", deviceName, deviceType);
        return createDevice(deviceName, deviceType);
    }

    // NEW: Create devices with conflict detection
    public DeviceCreationResult createDevicesWithConflictCheck(int startIdx, int endIdx, String deviceType) {
        DeviceCreationResult result = new DeviceCreationResult();

        for (int i = startIdx; i <= endIdx; i++) {
            String deviceName = "DW" + String.format("%08d", i);

            if (discoveryService.deviceExists(deviceName)) {
                result.addSkipped(deviceName);
                log.warn("Skipping existing device: '{}'", deviceName);
            } else {
                String deviceId = createDevice(deviceName, deviceType);
                if (deviceId != null) {
                    result.addCreated(deviceName, deviceId);
                    log.info("Created device: '{}'", deviceName);
                } else {
                    result.addFailed(deviceName);
                    log.error("Failed to create device: '{}'", deviceName);
                }
            }
        }

        return result;
    }
}
```

### **Change 3: Enhanced Test Executors**
**Modification to:** `src/main/java/org/thingsboard/tools/service/shared/AbstractAPITest.java`

```java
public abstract class AbstractAPITest {

    @Autowired
    protected EntityDiscoveryService discoveryService;

    // Existing createEntities method enhanced with existence checking
    protected void createEntities(int startIdx, int endIdx, boolean isGateway, boolean setCredentials) throws Exception {
        log.info("=== Entity Creation Phase ===");

        // Check for existing entities first
        checkExistingEntities(startIdx, endIdx, isGateway);

        // Continue with existing creation logic
        int entityCount = endIdx - startIdx + 1;
        log.info("Planning to create {} entities from index {} to {}", entityCount, startIdx, endIdx);

        for (int i = startIdx; i <= endIdx; i++) {
            String entityName = isGateway ? "GW" : "DW";
            entityName += String.format("%08d", i);

            // NEW: Skip if already exists
            if (discoveryService.deviceExists(entityName)) {
                log.warn("⚠️  Entity '{}' already exists - SKIPPING creation", entityName);
                continue;
            }

            try {
                String entityId = createSingleEntity(entityName, isGateway, setCredentials);
                log.info("✓ Created {}: {}", isGateway ? "gateway" : "device", entityName);
            } catch (Exception e) {
                log.error("✗ Failed to create {}: {}", isGateway ? "gateway" : "device", entityName, e);
                throw e;
            }
        }
    }

    // NEW: Check existing entities and provide guidance
    private void checkExistingEntities(int startIdx, int endIdx, boolean isGateway) {
        log.info("Checking for existing entities...");

        boolean hasHierarchy = discoveryService.hasHierarchicalAssets();
        if (hasHierarchy) {
            log.info("📊 Detected hierarchical assets (likely created by Python scripts)");
            log.info("💡 This suggests you may be running after a Python provision scenario");
            log.info("💡 Consider using higher device indices to avoid conflicts");
        }

        // Count existing entities in our range
        String prefix = isGateway ? "GW" : "DW";
        int existingCount = 0;
        for (int i = startIdx; i <= endIdx; i++) {
            String entityName = prefix + String.format("%08d", i);
            if (discoveryService.deviceExists(entityName)) {
                existingCount++;
            }
        }

        if (existingCount > 0) {
            log.warn("⚠️  Found {} existing entities in range {}-{}", existingCount, startIdx, endIdx);
            log.warn("💡 Use DEVICE_START_IDX > {} to avoid conflicts", endIdx);
        } else {
            log.info("✓ No existing entities found in range {}-{}", startIdx, endIdx);
        }
    }
}
```

### **Change 4: Enhanced Base Test Executor**
**Modification to:** `src/main/java/org/thingsboard/tools/service/shared/BaseTestExecutor.java`

```java
@Component
public abstract class BaseTestExecutor implements TestExecutor {

    @Autowired
    protected EntityDiscoveryService discoveryService;

    // Enhanced init method with ecosystem detection
    @Override
    public void init() throws Exception {
        log.info("=== Performance Test Initialization ===");

        // NEW: Detect existing ecosystem
        detectAndLogEcosystem();

        authenticate();

        if (entityCreationEnabled) {
            initEntities();
        }

        initDeviceProfiles();
        initRuleChain();
    }

    // NEW: Analyze and log current ecosystem state
    private void detectAndLogEcosystem() throws Exception {
        log.info("🔍 Analyzing current ThingsBoard ecosystem...");

        // Check for hierarchical assets (Python creation)
        boolean hasHierarchy = discoveryService.hasHierarchicalAssets();
        if (hasHierarchy) {
            log.info("📁 Hierarchical assets detected - likely Python provisioned scenario");
            log.info("   - Sites: {}", discoveryService.findAssetsByType("Site").size());
            log.info("   - Buildings: {}", discoveryService.findAssetsByType("Building").size());
            log.info("   - Rooms: {}", discoveryService.findAssetsByType("Room").size());
        } else {
            log.info("🏗️  No hierarchical assets detected - clean environment");
        }

        // Count existing devices
        int existingDevices = countExistingDevices();
        log.info("🔌 Existing devices found: {}", existingDevices);

        // Count existing gateways
        int existingGateways = countExistingGateways();
        log.info("🌐 Existing gateways found: {}", existingGateways);

        // Provide usage guidance
        if (hasHierarchy && existingDevices > 0) {
            log.info("💡 RECOMMENDATION: Use higher device indices to avoid conflicts with Python-created devices");
            log.info("💡 Example: export DEVICE_START_IDX=1000");
        }
    }

    private int countExistingDevices() throws Exception {
        // Simple count - could be enhanced with pagination for large numbers
        return restClientService.getDeviceCount();
    }

    private int countExistingGateways() throws Exception {
        // Count devices with "Gateway" type
        return restClientService.getDevicesByType("Gateway").size();
    }
}
```

### **Change 5: Configuration Guidelines**
**New File:** `COORDINATION_GUIDELINES.md`

```markdown
# Performance Test Setup Guidelines

## Quick Reference

### 1. Simple Performance Tests (No Hierarchy)
```bash
export DEVICE_START_IDX=0
export DEVICE_END_IDX=100
export GATEWAY_CREATE_ON_START=false
mvn spring-boot:run
```

### 2. Hierarchical Tests (Python + Java)
```bash
# Step 1: Create hierarchy with Python
python test-scenarios/provision-scenario.py scenarios/cleanroom.json

# Step 2: Run performance tests with Java (use higher indices to avoid conflicts)
export DEVICE_START_IDX=1000
export DEVICE_END_IDX=1100
mvn spring-boot:run
```

### 3. Clean Environment
```bash
# Remove all existing entities first
python test-scenarios/cleanup-scenario.py --all
# OR use cleanup script
./scripts/cleanup/clean-all.sh
```

## Conflict Prevention

### Device Naming Conventions
- **Python-created devices:** DW00000000, DW00000001, etc.
- **Java-created devices:** Use DEVICE_START_IDX > 1000 when Python was used

### Detection Features
The Java application now automatically detects:
- Existing hierarchical assets (Python-created)
- Device name conflicts
- Recommended index ranges
```

### **Change 6: Enhanced Cleanup Script**
**New File:** `scripts/cleanup/coordinated-cleanup.sh`

```bash
#!/bin/bash

echo "=== Coordinated Cleanup Script ==="

# Configuration
REST_URL=${REST_URL:-http://localhost:8080}
REST_USERNAME=${REST_USERNAME:-tenant@thingsboard.org}
REST_PASSWORD=${REST_PASSWORD:-tenant}

echo "Cleaning up performance test artifacts..."
echo "URL: $REST_URL"
echo "User: $REST_USERNAME"

# Login and get token
TOKEN=$(curl -s -X POST "$REST_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$REST_USERNAME\",\"password\":\"$REST_PASSWORD\"}" | \
  jq -r '.token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed"
    exit 1
fi

echo "✓ Authentication successful"

# Clean up in safe order
echo ""
echo "🧹 Cleaning up test devices..."

# Remove devices with DW prefix (test devices)
DEVICE_IDS=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000" \
  -H "X-Authorization: Bearer $TOKEN" | \
  jq -r '.data[] | select(.name | startswith("DW")) | .id.id')

DEVICE_COUNT=$(echo "$DEVICE_IDS" | wc -l)
echo "Found $DEVICE_COUNT test devices to remove"

for DEVICE_ID in $DEVICE_IDS; do
    if [ -n "$DEVICE_ID" ] && [ "$DEVICE_ID" != "null" ]; then
        echo "  Removing device: $DEVICE_ID"
        curl -s -X DELETE "$REST_URL/api/device/$DEVICE_ID" \
          -H "X-Authorization: Bearer $TOKEN" > /dev/null
    fi
done

# Remove test gateways
echo ""
echo "🌐 Cleaning up test gateways..."

GATEWAY_IDS=$(curl -s -X GET "$REST_URL/api/tenant/devices?pageSize=1000" \
  -H "X-Authorization: Bearer $TOKEN" | \
  jq -r '.data[] | select(.name | startswith("GW")) | .id.id')

GATEWAY_COUNT=$(echo "$GATEWAY_IDS" | wc -l)
echo "Found $GATEWAY_COUNT test gateways to remove"

for GATEWAY_ID in $GATEWAY_IDS; do
    if [ -n "$GATEWAY_ID" ] && [ "$GATEWAY_ID" != "null" ]; then
        echo "  Removing gateway: $GATEWAY_ID"
        curl -s -X DELETE "$REST_URL/api/device/$GATEWAY_ID" \
          -H "X-Authorization: Bearer $TOKEN" > /dev/null
    fi
done

# Summary
echo ""
echo "✅ Cleanup completed successfully"
echo "📊 Summary:"
echo "  - Removed $DEVICE_COUNT test devices"
echo "  - Removed $GATEWAY_COUNT test gateways"
echo ""
echo "💡 Note: Assets (Sites, Buildings, etc.) were preserved"
echo "💡 Use Python cleanup script to remove hierarchical assets if needed"
```

## Implementation Plan (3 Weeks)

### **Week 1: Foundation**
- [ ] Create EntityDiscoveryService with basic existence checking
- [ ] Create DeviceCreationResult and DeviceInfo data classes
- [ ] Add basic logging for entity detection
- [ ] Unit tests for discovery functionality

### **Week 2: Integration**
- [ ] Modify DeviceManager with conflict checking
- [ ] Enhance AbstractAPITest with existence checking
- [ ] Update BaseTestExecutor with ecosystem detection
- [ ] Integration tests for enhanced test executors

### **Week 3: Documentation and Cleanup**
- [ ] Create coordination guidelines documentation
- [ ] Create enhanced cleanup script
- [ ] Update existing documentation with new guidelines
- [ ] End-to-end testing of hybrid workflow

## Usage Examples

### **Example 1: Simple Performance Test**
```bash
# User wants to run a simple test with 100 devices
export DEVICE_START_IDX=0
export DEVICE_END_IDX=99
export MESSAGES_PER_SECOND=50

# Java app will:
# 1. Detect clean environment (no hierarchy)
# 2. Create 100 devices from DW00000000 to DW00000099
# 3. Run performance test
mvn spring-boot:run
```

### **Example 2: Hierarchical Test Setup**
```bash
# Step 1: User creates hierarchical scenario with Python
python test-scenarios/provision-scenario.py scenarios/cleanroom.json
# Creates: Site -> Building -> Floor -> Room -> Gateway + 60 Devices

# Step 2: User runs performance test
export DEVICE_START_IDX=1000  # Avoid conflicts
export DEVICE_END_IDX=1099
export MESSAGES_PER_SECOND=100

# Java app will:
# 1. Detect hierarchical assets (Python-created)
# 2. Warn about potential conflicts
# 3. Create 100 NEW devices from DW00001000 to DW00001099
# 4. Run performance test
mvn spring-boot:run
```

### **Example 3: Cleanup**
```bash
# After testing, user wants to clean up
./scripts/cleanup/coordinated-cleanup.sh

# Output:
# 🧹 Cleaning up test devices...
# Found 160 test devices to remove
# ✅ Cleanup completed successfully
# 💡 Assets were preserved
```

## Logging Improvements

### **Before (Current)**
```
Creating entities from index 0 to 100
Created device: DW00000000
Created device: DW00000001
...
```

### **After (Enhanced)**
```
🔍 Analyzing current ThingsBoard ecosystem...
📁 Hierarchical assets detected - likely Python provisioned scenario
   - Sites: 1
   - Buildings: 1
   - Rooms: 5
🔌 Existing devices found: 60
🌐 Existing gateways found: 1
💡 RECOMMENDATION: Use higher device indices to avoid conflicts with Python-created devices
💡 Example: export DEVICE_START_IDX=1000

=== Entity Creation Phase ===
Checking for existing entities...
⚠️  Found 10 existing entities in range 0-99
💡 Use DEVICE_START_IDX > 99 to avoid conflicts
⚠️  Entity 'DW00000000' already exists - SKIPPING creation
✓ Created device: DW00000010
...
```

## Risk Mitigation

### **Technical Risks (Very Low)**
- **No Breaking Changes:** All existing functionality preserved
- **Incremental:** Changes are additive, not replacements
- **Rollback:** Easy to disable if issues arise

### **User Experience Risks (Low)**
- **Confusion:** Clear logging and documentation
- **Migration:** Existing workflows continue to work
- **Learning:** Simple guidelines and examples

## Success Metrics

### **Immediate (Week 1)**
- [ ] Zero breaking changes to existing functionality
- [ ] Entity detection works reliably
- [ ] Clear logging provides useful information

### **Short-term (Week 3)**
- [ ] Users can avoid entity conflicts
- [ ] Cleanup scripts work correctly
- [ ] Documentation is clear and helpful

### **Long-term**
- [ ] Reduced user confusion about system usage
- [ ] Fewer duplicate entity issues reported
- [ ] Better test isolation and repeatability

## Future Evolution Path

This Option 3 implementation provides a solid foundation that can evolve toward Option 1 (Unified Entity Management) if needed:

### **Phase 1: Coordination (This Plan)**
- Basic conflict detection
- Entity discovery
- Better logging

### **Phase 2: Integration (Future)**
- Shared naming conventions
- State synchronization
- Cross-system configuration

### **Phase 3: Unification (Future - Option 1)**
- Full asset management in Java
- Unified configuration schema
- Single cleanup mechanism

## Rollback Plan

If any issues arise:
1. **Disable Discovery:** Set environment variable `ENTITY_DISCOVERY_ENABLED=false`
2. **Remove Logging:** Comment out enhanced logging in test executors
3. **Fallback:** All existing functionality works without the new features

## Next Steps

1. **Review and approve** this minimal change plan
2. **Set up development branch** for the coordination features
3. **Implement EntityDiscoveryService** (Week 1)
4. **Test with existing scenarios** to ensure no regressions
5. **Create documentation** and guidelines
6. **Deploy and monitor** user feedback

---

**Document Version:** 1.0
**Author:** Claude Code Assistant
**Date:** 2025-01-21
**Status:** Ready for Implementation
**Effort Level:** Low (2-3 weeks)
**Risk Level:** Very Low
**Backward Compatibility:** Full