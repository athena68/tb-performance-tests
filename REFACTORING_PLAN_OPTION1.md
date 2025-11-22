# Refactoring Plan: Unified Entity Management (Option 1)

## Executive Summary

This refactoring will integrate asset creation capabilities into the Java Spring Boot application, unifying the currently separate Python and Java entity creation systems into a single, coherent framework. The goal is to eliminate architectural inconsistencies while supporting both simple performance tests and complex hierarchical scenarios.

## Current Problems Being Solved

### 1. **Two Separate Creation Systems**
- Java app: Creates devices, gateways, customers, dashboards (flat structure)
- Python scripts: Creates assets, devices, gateways (hierarchical structure)
- No coordination or conflict detection between systems

### 2. **Configuration Fragmentation**
- Environment variables for Java configuration
- JSON files for Python scenarios
- No single source of truth

### 3. **Cleanup Complexity**
- Java cleanup via environment flags
- Python cleanup via separate scripts
- Potential for orphaned entities

### 4. **User Confusion**
- Unclear when to use which system
- Risk of duplicate entities
- Complex setup and teardown processes

## Refactoring Architecture

### New Unified Entity Management System

```
┌─────────────────────────────────────────────────────────────┐
│                Unified Configuration Layer                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   YAML/JSON     │  │ Environment     │  │ Command Line │ │
│  │   Scenarios     │  │ Variables       │  │ Arguments    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│               Enhanced Service Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  AssetManager   │  │ DeviceManager   │  │ RelationMgr  │ │
│  │  (NEW)          │  │  (Enhanced)     │  │  (NEW)       │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ CustomerManager │  │ DashboardManager│  │ Validation   │ │
│  │ (Existing)      │  │ (Existing)      │  │ Service      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                 Enhanced Test Executors                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ HierarchyTest   │  │ DeviceTest      │  │ GatewayTest  │ │
│  │ Executor        │  │ Executor        │  │ Executor     │ │
│  │ (NEW)           │  │ (Enhanced)      │  │ (Enhanced)   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Foundation - Asset Management Infrastructure

#### 1.1 Asset Manager Implementation
**File:** `src/main/java/org/thingsboard/tools/service/asset/AssetManager.java`

```java
@Service
public class AssetManager {

    @Autowired
    private RestClientService restClientService;

    @Autowired
    private RelationManager relationManager;

    @Autowired
    private ValidationService validationService;

    // Core asset creation methods
    public String createAsset(String name, String type, Map<String, Object> attributes);
    public boolean updateAsset(String assetId, Map<String, Object> attributes);
    public boolean deleteAsset(String assetId);
    public Optional<Asset> findAssetByName(String name);
    public List<Asset> getAssetsByType(String type);

    // Hierarchy-specific methods
    public String createSite(String name, SiteAttributes attributes);
    public String createBuilding(String name, String siteId, BuildingAttributes attributes);
    public String createFloor(String name, String buildingId, FloorAttributes attributes);
    public String createRoom(String name, String floorId, RoomAttributes attributes);
}
```

#### 1.2 Relation Manager Implementation
**File:** `src/main/java/org/thingsboard/tools/service/relation/RelationManager.java`

```java
@Service
public class RelationManager {

    @Autowired
    private RestClientService restClientService;

    // Relation management methods
    public boolean createRelation(String fromId, String fromType, String toId, String toType, String relationType);
    public boolean deleteRelation(String fromId, String fromType, String toId, String toType, String relationType);
    public List<Relation> getRelations(String entityId, String entityType);
    public boolean createHierarchyRelation(String parentAsset, String childEntity, String relationType);
}
```

#### 1.3 Validation Service Implementation
**File:** `src/main/java/org/thingsboard/tools/service/validation/ValidationService.java`

```java
@Service
public class ValidationService {

    // Entity existence validation
    public boolean assetExists(String name);
    public boolean deviceExists(String name);
    public boolean gatewayExists(String name);

    // Hierarchy validation
    public ValidationResult validateScenario(UnifiedScenario scenario);
    public boolean validateHierarchyIntegrity(String rootAssetId);

    // Conflict detection
    public List<Conflict> detectEntityConflicts(UnifiedScenario scenario);
    public List<String> getOrphanedEntities();
}
```

#### 1.4 Asset Data Models
**Files:**
- `src/main/java/org/thingsboard/tools/service/asset/model/Asset.java`
- `src/main/java/org/thingsboard/tools/service/asset/model/SiteAttributes.java`
- `src/main/java/org/thingsboard/tools/service/asset/model/BuildingAttributes.java`
- `src/main/java/org/thingsboard/tools/service/asset/model/FloorAttributes.java`
- `src/main/java/org/thingsboard/tools/service/asset/model/RoomAttributes.java`

### Phase 2: Configuration Unification

#### 2.1 Unified Scenario Configuration
**File:** `src/main/resources/unified-scenario-schema.yaml`

```yaml
# Unified Scenario Configuration Schema
scenario:
  name: string
  description: string
  mode: enum [PERFORMANCE_TEST, HIERARCHICAL_TEST]

# Environment variables override
environment:
  REST_URL: string
  REST_USERNAME: string
  REST_PASSWORD: string
  MQTT_HOST: string
  TEST_API: enum [device, gateway]
  TEST_PAYLOAD_TYPE: enum [DEFAULT, SMART_TRACKER, SMART_METER, INDUSTRIAL_PLC, EBMPAPST_FFU]

# Entity creation control
entityCreation:
  createCustomers: boolean
  createAssets: boolean
  createGateways: boolean
  createDevices: boolean
  createDashboards: boolean
  createRelations: boolean
  conflictResolution: enum [SKIP, UPDATE, ERROR]

# Asset hierarchy definition
assetHierarchy:
  sites:
    - name: string
      type: string (default: "Site")
      attributes:
        address: string
        latitude: double
        longitude: double
        site_type: string
      buildings:
        - name: string
          type: string (default: "Building")
          attributes:
            address: string
            latitude: double
            longitude: double
            building_type: string
          floors:
            - name: string
              type: string (default: "Floor")
              rooms:
                - name: string
                  type: string (default: "Room")
                  attributes:
                    classification: string
                    area_sqm: double
                    floor_plan: string
                  gateways:
                    - name: string
                      type: string (default: "Gateway")
                      protocol: string (default: "MQTT")
                      devices:
                        count: integer
                        prefix: string (default: "DW")
                        start: integer
                        end: integer
                        layout: enum [grid, random]
                        gridColumns: integer
                        spacingX: double
                        spacingY: double

# Device configuration
deviceConfig:
  startIdx: integer
  endIdx: integer
  count: integer
  payloadType: string
  messagesPerSecond: integer

# Test execution parameters
testExecution:
  warmupEnabled: boolean
  warmupDuration: integer
  testDuration: integer
  messagesPerSecond: integer
  alarmsPerSecond: integer
```

#### 2.2 Configuration Loader
**File:** `src/main/java/org/thingsboard/tools/service/config/UnifiedConfigurationLoader.java`

```java
@Service
public class UnifiedConfigurationLoader {

    public UnifiedScenario loadScenario(String scenarioPath);
    public UnifiedScenario loadFromYaml(InputStream yamlStream);
    public UnifiedScenario loadFromJson(InputStream jsonStream);
    public UnifiedScenario mergeWithEnvironment(UnifiedScenario scenario);
    public void validateConfiguration(UnifiedScenario scenario);
}
```

### Phase 3: Enhanced Test Executors

#### 3.1 Hierarchy Test Executor
**File:** `src/main/java/org/thingsboard/tools/service/hierarchy/HierarchyTestExecutor.java`

```java
@Component
public class HierarchyTestExecutor extends BaseTestExecutor {

    @Autowired
    private AssetManager assetManager;

    @Autowired
    private RelationManager relationManager;

    @Autowired
    private ValidationService validationService;

    @Override
    public void initEntities() throws Exception {
        // Validate scenario for conflicts
        List<Conflict> conflicts = validationService.detectEntityConflicts(scenario);
        if (!conflicts.isEmpty()) {
            handleConflicts(conflicts);
        }

        // Create complete hierarchy
        createAssetHierarchy();

        // Create devices and gateways within hierarchy
        createDevicesInHierarchy();
    }

    private void createAssetHierarchy() throws Exception {
        for (SiteConfig siteConfig : scenario.getAssetHierarchy().getSites()) {
            String siteId = assetManager.createSite(siteConfig.getName(), siteConfig.getAttributes());
            createBuildingsForSite(siteId, siteConfig.getBuildings());
        }
    }

    private void createBuildingsForSite(String siteId, List<BuildingConfig> buildings) throws Exception {
        for (BuildingConfig buildingConfig : buildings) {
            String buildingId = assetManager.createBuilding(buildingConfig.getName(), siteId, buildingConfig.getAttributes());
            createFloorsForBuilding(buildingId, buildingConfig.getFloors());
        }
    }

    // ... additional hierarchy creation methods
}
```

#### 3.2 Enhanced Base Test Executor
**Modifications to:** `src/main/java/org/thingsboard/tools/service/shared/BaseTestExecutor.java`

```java
public abstract class BaseTestExecutor implements TestExecutor {

    @Autowired
    protected AssetManager assetManager;

    @Autowired
    protected RelationManager relationManager;

    @Autowired
    protected ValidationService validationService;

    @Autowired
    protected UnifiedConfigurationLoader configLoader;

    protected UnifiedScenario unifiedScenario;

    @Override
    public void init() throws Exception {
        // Load unified scenario
        if (scenarioPath != null) {
            unifiedScenario = configLoader.loadScenario(scenarioPath);
            unifiedScenario = configLoader.mergeWithEnvironment(unifiedScenario);
        }

        // Validate configuration
        if (unifiedScenario != null) {
            configLoader.validateConfiguration(unifiedScenario);
        }

        // Continue with existing initialization
        authenticate();

        if (entityCreationEnabled) {
            initEntities();
        }

        initDeviceProfiles();
        initRuleChain();
    }

    @Override
    public void cleanup() throws Exception {
        // Enhanced cleanup with hierarchy support
        if (unifiedScenario != null && unifiedScenario.getEntityCreation().isDeleteOnComplete()) {
            cleanupHierarchicalEntities();
        }

        // Continue with existing cleanup
        revertRuleChain();
    }

    protected void cleanupHierarchicalEntities() throws Exception {
        // Clean up in reverse order: devices -> gateways -> rooms -> floors -> buildings -> sites
        cleanupDevices();
        cleanupGateways();
        cleanupAssets();
        cleanupRelations();
    }
}
```

### Phase 4: Migration of Python Logic

#### 4.1 Asset Creation Logic Migration
**Mapping from Python `create_asset()` to Java:**

```python
# Python: test-scenarios/provision-scenario.py:125
def create_asset(self, name: str, asset_type: str, label: str, attributes: Dict[str, any]) -> Optional[str]:
    # Python implementation with REST calls
```

**Becomes Java Implementation:**
```java
// Java: AssetManager.java
public String createAsset(String name, String type, String label, Map<String, Object> attributes) {
    Asset asset = new Asset();
    asset.setName(name);
    asset.setType(type);
    asset.setLabel(label);
    asset.setAttributes(attributes);

    return restClientService.createAsset(asset);
}
```

#### 4.2 Hierarchy Creation Pattern Migration
**Python Pattern (lines 449-534 in provision-scenario.py):**
```python
site = self.create_asset(site_config['name'], site_config.get('type', 'Site'), ...)
building = self.create_asset(building_config['name'], building_config.get('type', 'Building'), ...)
self.create_relation(site, 'ASSET', building, 'ASSET')
```

**Java Pattern:**
```java
String siteId = assetManager.createSite(siteConfig.getName(), siteConfig.getAttributes());
String buildingId = assetManager.createBuilding(buildingConfig.getName(), siteId, buildingConfig.getAttributes());
relationManager.createHierarchyRelation(siteId, buildingId, "CONTAINS");
```

#### 4.3 Device Creation Enhancement
**Enhancement to existing DeviceManager:**
```java
public class DeviceManager {

    // Existing methods remain...

    // New hierarchical device creation
    public String createDeviceInHierarchy(String deviceName, String deviceType, String parentRoomId, DeviceConfig config) {
        String deviceId = createDevice(deviceName, deviceType);

        // Create relation with parent room
        relationManager.createHierarchyRelation(parentRoomId, deviceId, "CONTAINS_DEVICE");

        return deviceId;
    }

    // Enhanced device positioning
    public void setDevicePosition(String deviceId, double x, double y) {
        Map<String, Object> positionAttrs = Map.of(
            "x_position", x,
            "y_position", y
        );
        addDeviceAttributes(deviceId, positionAttrs);
    }
}
```

### Phase 5: Conflict Detection and Resolution

#### 5.1 Entity Conflict Detection
**File:** `src/main/java/org/thingsboard/tools/service/validation/ConflictDetectionService.java`

```java
@Service
public class ConflictDetectionService {

    public List<EntityConflict> detectConflicts(UnifiedScenario scenario) {
        List<EntityConflict> conflicts = new ArrayList<>();

        // Check for existing assets
        for (SiteConfig site : scenario.getAssetHierarchy().getSites()) {
            if (validationService.assetExists(site.getName())) {
                conflicts.add(new EntityConflict(
                    EntityType.ASSET,
                    site.getName(),
                    ConflictType.EXISTS,
                    ResolutionStrategy.OPTIONAL
                ));
            }
        }

        // Check for existing devices
        checkDeviceConflicts(scenario, conflicts);

        return conflicts;
    }

    public enum ResolutionStrategy {
        SKIP,           // Don't create if exists
        UPDATE,         // Update existing entity
        ERROR,          // Fail on conflict
        DELETE_REPLACE  // Delete existing and create new
    }
}
```

#### 5.2 Conflict Resolution Strategy
**File:** `src/main/java/org/thingsboard/tools/service/conflict/ConflictResolver.java`

```java
@Service
public class ConflictResolver {

    public void resolveConflicts(List<EntityConflict> conflicts, ResolutionStrategy strategy) throws Exception {
        for (EntityConflict conflict : conflicts) {
            switch (strategy) {
                case SKIP:
                    // Skip creation of conflicting entities
                    skipEntityCreation(conflict);
                    break;
                case UPDATE:
                    // Update existing entities with new configuration
                    updateEntity(conflict);
                    break;
                case ERROR:
                    // Throw exception to halt execution
                    throw new EntityConflictException("Entity conflict detected: " + conflict.getEntityName());
                case DELETE_REPLACE:
                    // Delete existing entity and create new one
                    replaceEntity(conflict);
                    break;
            }
        }
    }
}
```

### Phase 6: Enhanced Cleanup Mechanisms

#### 6.1 Hierarchical Cleanup Service
**File:** `src/main/java/org/thingsboard/tools/service/cleanup/HierarchicalCleanupService.java`

```java
@Service
public class HierarchicalCleanupService {

    public void cleanupScenario(UnifiedScenario scenario) throws Exception {
        // Clean up in reverse dependency order
        cleanupDevices(scenario);
        cleanupGateways(scenario);
        cleanupAssets(scenario);
        cleanupRelations(scenario);
    }

    private void cleanupAssets(UnifiedScenario scenario) throws Exception {
        // Clean up rooms, floors, buildings, sites in reverse order
        for (SiteConfig site : scenario.getAssetHierarchy().getSites()) {
            for (BuildingConfig building : site.getBuildings()) {
                for (FloorConfig floor : building.getFloors()) {
                    // Clean up rooms first
                    for (RoomConfig room : floor.getRooms()) {
                        assetManager.deleteAssetByName(room.getName());
                    }
                    assetManager.deleteAssetByName(floor.getName());
                }
                assetManager.deleteAssetByName(building.getName());
            }
            assetManager.deleteAssetByName(site.getName());
        }
    }
}
```

## Migration Strategy

### Phase 1: Foundation (Weeks 1-2)
- [ ] Implement AssetManager, RelationManager, ValidationService
- [ ] Create asset data models and attributes
- [ ] Unit tests for all new services

### Phase 2: Configuration (Weeks 3-4)
- [ ] Design and implement unified configuration schema
- [ ] Create UnifiedConfigurationLoader
- [ ] Migrate existing configuration formats
- [ ] Configuration validation tests

### Phase 3: Test Executors (Weeks 5-6)
- [ ] Implement HierarchyTestExecutor
- [ ] Enhance BaseTestExecutor
- [ ] Integration tests for new executors

### Phase 4: Migration (Weeks 7-8)
- [ ] Migrate Python asset creation logic to Java
- [ ] Migrate hierarchy creation patterns
- [ ] Enhance device creation with positioning
- [ ] End-to-end migration tests

### Phase 5: Conflict Management (Weeks 9-10)
- [ ] Implement conflict detection
- [ ] Create resolution strategies
- [ ] Add conflict handling to test executors
- [ ] Conflict scenario tests

### Phase 6: Cleanup and Documentation (Weeks 11-12)
- [ ] Implement hierarchical cleanup
- [ ] Create migration utilities
- [ ] Update documentation
- [ ] Performance testing and optimization

## Configuration Examples

### Simple Performance Test (Current Java App Usage)
```yaml
scenario:
  name: "Simple MQTT Performance Test"
  mode: "PERFORMANCE_TEST"

entityCreation:
  createAssets: false
  createDevices: true
  createGateways: false

deviceConfig:
  startIdx: 0
  endIdx: 1000
  messagesPerSecond: 50

testExecution:
  testDuration: 300
  messagesPerSecond: 50
```

### Hierarchical Test (Current Python Script Usage)
```yaml
scenario:
  name: "Cleanroom FFU Performance Test"
  mode: "HIERARCHICAL_TEST"

entityCreation:
  createAssets: true
  createDevices: true
  createGateways: true
  createRelations: true

assetHierarchy:
  sites:
    - name: "EBMPAPST Test Site"
      buildings:
        - name: "Cleanroom Building"
          floors:
            - name: "Cleanroom Floor"
              rooms:
                - name: "Server Room"
                  gateways:
                    - name: "GW00000000"
                      devices:
                        count: 60
                        prefix: "DW"
                        start: 0
                        layout: "grid"
                        gridColumns: 6
```

## Backward Compatibility

### Legacy Environment Variable Support
All existing environment variables will continue to work:
- `DEVICE_CREATE_ON_START` → maps to `entityCreation.createDevices`
- `GATEWAY_CREATE_ON_START` → maps to `entityCreation.createGateways`
- `DEVICE_START_IDX`, `DEVICE_END_IDX` → maps to `deviceConfig.startIdx`, `deviceConfig.endIdx`

### Legacy Configuration Files
Existing configuration files will be supported with automatic migration:
- `tb-ce-performance-tests.yml` → unified format conversion
- JSON scenario files → unified schema validation

## Testing Strategy

### Unit Tests
- All new service components with >90% coverage
- Configuration loading and validation
- Conflict detection and resolution
- Asset hierarchy creation

### Integration Tests
- End-to-end scenario provisioning
- Performance test execution with hierarchy
- Conflict resolution scenarios
- Cleanup and tear-down processes

### Migration Tests
- Python-to-Java logic migration validation
- Configuration format migration
- Backward compatibility verification

### Performance Tests
- Large hierarchy creation (>1000 assets)
- Memory usage during creation
- Test execution impact with hierarchy

## Risk Mitigation

### Technical Risks
1. **Complexity Risk:** Hierarchical creation adds complexity
   - **Mitigation:** Comprehensive testing, gradual rollout, feature flags

2. **Performance Risk:** Additional overhead might affect performance testing
   - **Mitigation:** Lazy loading, optional hierarchy creation, performance benchmarks

3. **Migration Risk:** Data loss during transition
   - **Mitigation:** Backup utilities, rollback procedures, migration validation

### Business Risks
1. **Disruption Risk:** Existing workflows might break
   - **Mitigation:** Backward compatibility, gradual migration, clear documentation

2. **Learning Risk:** Users need to learn new configuration format
   - **Mitigation:** Migration utilities, examples, training materials

## Success Metrics

### Technical Metrics
- [ ] Zero regression in existing functionality
- [ ] <5% performance overhead for simple tests
- [ ] >90% test coverage for new components
- [ ] <2 second hierarchy creation time for typical scenarios

### Business Metrics
- [ ] Single configuration file for all test types
- [ ] Elimination of duplicate entity creation
- [ ] Reduced setup time for complex scenarios
- [ ] Improved test repeatability and isolation

## Rollback Plan

If critical issues are discovered:
1. **Feature Flags:** Disable hierarchy creation via configuration
2. **Legacy Mode:** Fall back to existing executors
3. **Configuration Migration:** Convert unified config back to legacy format
4. **Data Recovery:** Restore from pre-migration backups

## Next Steps

1. **Review this plan** with architecture team
2. **Approve implementation timeline** with stakeholders
3. **Set up development branch** for refactoring work
4. **Create PoC** for AssetManager and basic hierarchy creation
5. **Define test scenarios** for validation and performance testing

---

**Document Version:** 1.0
**Author:** Claude Code Assistant
**Date:** 2025-01-21
**Status:** Pending Review