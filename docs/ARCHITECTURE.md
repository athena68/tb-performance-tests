# Architecture Documentation

## Overview

This document consolidates all architecture decisions, refactoring plans, and design patterns used in the ThingsBoard Performance Tests project.

## Project Structure

```
performance-tests/
├── src/main/java/org/thingsboard/tools/
│   ├── PerformanceTestApplication.java    # Spring Boot main entry
│   ├── PerformanceTestRunner.java         # Test orchestrator
│   └── service/
│       ├── shared/                        # Base test infrastructure
│       ├── device/                        # Device API tests
│       ├── gateway/                       # Gateway API tests
│       ├── mqtt/                          # MQTT client
│       └── msg/                           # Message generators
│
├── test-scenarios/                        # Python provisioning scripts
│   ├── provision-scenario.py              # Main provisioning script
│   ├── cleanup-scenario.py                # Cleanup script
│   └── scenario-*.json                    # Scenario configurations
│
├── scripts/test-runners/                  # Shell test runners
│   └── start-ebmpapst-gateway.sh          # Gateway test runner
│
└── config/                                # Configuration files
    └── attributes/                        # Configurable attribute templates
```

## Architecture Decisions

### 1. Configurable Attributes System

**Decision**: Use external YAML templates for device/asset attributes instead of hardcoding values.

**Rationale**:
- Flexibility: Easy to modify attributes without code changes
- Reusability: Share attribute templates across scenarios
- Maintainability: Centralized attribute definitions

**Implementation**: `config/attributes/` directory with YAML files for each entity type.

### 2. Scenario-Based Provisioning

**Decision**: JSON scenario files drive entity creation and configuration.

**Rationale**:
- Declarative: Define what you want, not how to create it
- Version control: Track infrastructure as code
- Reproducibility: Same scenario creates identical setup

**Implementation**: `test-scenarios/scenario-*.json` files processed by `provision-scenario.py`.

### 3. Gateway-Based Testing

**Decision**: Support both direct device testing and gateway-mediated testing.

**Rationale**:
- Real-world scenarios: Many IoT deployments use gateways
- Scalability testing: Test gateway capacity limits
- Protocol flexibility: Gateways can aggregate multiple protocols

**Implementation**:
- `MqttGatewayAPITest.java` for gateway testing
- `MqttDeviceAPITest.java` for direct device testing

### 4. Access Token Management

**Decision**: Use device/gateway name as access token for testing.

**Rationale**:
- Predictability: Token = name makes debugging easier
- Automation: Java app can derive tokens from device indices
- Consistency: Same pattern for gateways and devices

**Implementation**: `provision-scenario.py` sets credentials via ThingsBoard REST API.

## Payload Types

The system supports multiple payload types for different use cases:

### EBMPAPST_FFU
Fan Filter Unit telemetry with realistic industrial data:
- Fan speed, power consumption, pressure
- Filter status, runtime hours
- Temperature, humidity, airflow

### SMART_TRACKER
GPS tracker telemetry:
- Latitude, longitude, speed
- Fuel level, battery level

### SMART_METER
Utility meter telemetry:
- Pulse counter, leakage status
- Battery level

### INDUSTRIAL_PLC
Industrial sensors with configurable datapoints:
- Configurable number of data channels
- Numeric sensor readings

## Test Lifecycle

1. **Initialization**: Connect to ThingsBoard REST API, authenticate
2. **Device Profile Creation**: Create device profiles based on payload type
3. **Entity Creation** (optional): Create customers, dashboards, devices, gateways
4. **Rule Chain Update** (optional): Replace root rule chain with test-specific chain
5. **Warmup** (optional): Send initial batch of messages to warm up connections
6. **Test Execution**: Publish messages at configured rate for specified duration
7. **Cleanup**: Revert rule chains, delete created entities (if configured)
8. **Shutdown**: Close connections and exit

## Environment Configuration

Configuration via environment variables or `.env` file:

```bash
# Connection
REST_URL=http://localhost:8080
REST_USERNAME=tenant@thingsboard.org
REST_PASSWORD=tenant
MQTT_HOST=localhost
MQTT_PORT=1883

# Test Parameters
TEST_API=gateway                    # device or gateway
DEVICE_API=MQTT                     # MQTT, HTTP, or LWM2M
TEST_PAYLOAD_TYPE=EBMPAPST_FFU     # Payload type
GATEWAY_START_IDX=0
GATEWAY_END_IDX=1
GATEWAY_COUNT=2
DEVICE_START_IDX=0
DEVICE_END_IDX=59
DEVICE_COUNT=60
MESSAGES_PER_SECOND=60
DURATION_IN_SECONDS=86400

# Lifecycle Control
DEVICE_CREATE_ON_START=false
DEVICE_DELETE_ON_COMPLETE=false
WARMUP_ENABLED=true
UPDATE_ROOT_RULE_CHAIN=false
REVERT_ROOT_RULE_CHAIN=false
```

## Refactoring History

### Option 3: Configurable Attributes (Implemented)

Moved from hardcoded attributes to YAML-based templates with:
- Attribute inheritance and composition
- Context-aware attribute generation
- Fallback to defaults when templates unavailable

This approach was chosen over:
- **Option 1**: Complete rewrite (too risky, high effort)
- **Option 2**: Minimal changes (insufficient flexibility)

### Security Refactoring

- Removed hardcoded credentials from codebase
- Moved to `test-scenarios/credentials.json` (gitignored)
- Added credential loading utilities
- Secured all Python scripts to use credentials file

## Future Considerations

### Scalability
- Consider distributed testing across multiple machines
- Add support for cloud-based ThingsBoard deployments
- Implement dynamic device scaling during tests

### Monitoring
- Add Prometheus metrics export
- Create Grafana dashboards for test visualization
- Implement real-time test progress tracking

### Testing
- Add integration tests for provisioning scripts
- Create unit tests for message generators
- Implement end-to-end test scenarios
