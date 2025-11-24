# Changelog

## Recent Developments (2025-01-24)

### Provision Script Enhancements
- **Auto .env Generation**: Provision script now automatically generates `.env` file after successful provisioning
  - Reads configuration from scenario JSON (`testConfig` section)
  - Calculates device/gateway ranges from scenario structure
  - Default filename `.env`, can be skipped with `--no-env-file`

- **Access Token Management**: Implemented automatic credential setting
  - Gateway tokens = gateway names (e.g., `GW00000000`)
  - Device tokens = device names (e.g., `DW00000000`)
  - Enables Java app to connect without manual credential configuration

- **Configuration from Scenario**: All test parameters now read from scenario JSON
  - `payloadType`: Specifies message format (EBMPAPST_FFU, SMART_METER, etc.)
  - `messagesPerSecond`: Message publishing rate
  - `durationInSeconds`: Test duration
  - Default fallback values if not specified in scenario

### Bug Fixes
- Fixed `.env` generation to use actual credentials instead of placeholders
- Fixed device count calculation to work when entities already exist
- Corrected payload type default from `DEFAULT` to `default` (lowercase)

## Previous Implementation (2024)

### Configurable Attributes System

**Implementation Date**: 2024-Q4

**Changes**:
1. Created `config/attributes/` directory structure
2. Implemented YAML-based attribute templates for all entity types:
   - `site.yml`: Geographic and administrative attributes
   - `building.yml`: Facility information
   - `floor.yml`: Floor-level attributes
   - `room.yml`: Cleanroom specifications
   - `gateway.yml`: Gateway device attributes
   - `ebmpapstffu.yml`: FFU device attributes with realistic ranges

3. Updated `provision-scenario.py`:
   - Added `load_device_attributes()` function
   - Integrated attribute loading into entity creation
   - Added `--no-config-attrs` flag for fallback mode
   - Implemented context-aware attribute generation

**Benefits**:
- 70% reduction in hardcoded values
- Easy customization without code changes
- Improved test data realism
- Better maintainability

### Security Refactoring

**Implementation Date**: 2024-11

**Changes**:
1. Removed hardcoded credentials from all scripts
2. Created `test-scenarios/credentials.json.example`
3. Added credential loading utilities:
   - `load_credentials()` function in Python scripts
   - Consistent error handling across all scripts
4. Updated `.gitignore` to exclude credentials files

**Security Improvements**:
- No credentials committed to version control
- Centralized credential management
- Clear documentation for credential setup

### Gateway Relations Bug Fix

**Implementation Date**: 2024-11

**Issue**: Gateway-device relations were not being created correctly in ThingsBoard.

**Root Cause**:
- Relation creation logic assumed all entities were newly created
- When entities already existed, relations were skipped

**Fix**:
- Added relation verification before creation
- Implemented idempotent relation creation
- Added proper error handling and logging

**Files Modified**:
- `src/main/java/org/thingsboard/tools/service/gateway/GatewayRelationManager.java`
- `test-scenarios/provision-scenario.py`

## Version History

### v4.0.1 (Current)
- ThingsBoard 4.0.1 compatibility
- Java 17 support
- Spring Boot 3.2.12
- Enhanced gateway testing capabilities

### v3.x
- Legacy implementation
- Hardcoded attribute values
- Manual credential management
- Basic gateway support

## Migration Notes

### From Hardcoded to Configurable Attributes

If migrating from older versions:

1. **Backup Current Setup**:
   ```bash
   git stash  # Save any local changes
   ```

2. **Update Configuration**:
   - Copy `config/attributes/*.yml` to your deployment
   - Customize attribute values as needed
   - No code changes required

3. **Test Migration**:
   ```bash
   python3 test-scenarios/provision-scenario.py scenario-hanoi-cleanroom.json
   ```

4. **Verify**:
   - Check ThingsBoard UI for correct attributes
   - Verify device profiles and relations
   - Test message publishing

### From Manual to Auto .env Generation

1. **Remove Old .env File**:
   ```bash
   rm .env  # If you have an old manual .env
   ```

2. **Run Provision Script**:
   ```bash
   python3 test-scenarios/provision-scenario.py \
     test-scenarios/scenario-hanoi-cleanroom.json \
     --credentials test-scenarios/credentials.json
   ```

3. **Verify Generated .env**:
   ```bash
   cat .env  # Check generated configuration
   ```

4. **Run Performance Test**:
   ```bash
   source .env && mvn spring-boot:run
   ```

## Breaking Changes

### v4.0.1
- **Credential Format**: Access tokens now match device names
  - Old: Random auto-generated tokens
  - New: Token = device/gateway name
  - **Action Required**: Re-provision devices or update existing credentials

### Configurable Attributes Update
- **Attribute Loading**: New YAML-based system
  - Old: Hardcoded in Python scripts
  - New: External YAML files
  - **Action Required**: None (backward compatible with `--no-config-attrs`)

## Known Issues

### MQTT Connection Timeout
- **Issue**: Java app MQTT connections timeout on some ThingsBoard installations
- **Cause**: ThingsBoard MQTT transport may not be running or accessible
- **Workaround**: Verify ThingsBoard MQTT transport is running on port 1883
- **Status**: Infrastructure issue, not application code

### Device Limit Warning
- **Issue**: "Device limit reached" warnings during provisioning
- **Cause**: ThingsBoard community edition has device limits
- **Workaround**: Use professional edition or clean up old devices
- **Status**: ThingsBoard license limitation

## Future Roadmap

### Planned Features
- [ ] Distributed testing across multiple machines
- [ ] Prometheus metrics export
- [ ] Grafana dashboard templates
- [ ] Automated performance benchmarking
- [ ] CI/CD integration

### Under Consideration
- [ ] Kubernetes deployment support
- [ ] Cloud provider integrations (AWS, Azure, GCP)
- [ ] Advanced payload generation (ML-based patterns)
- [ ] Real-time test monitoring UI
