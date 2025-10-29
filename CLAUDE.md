# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ThingsBoard Performance Tests is a Java-based Spring Boot application that stress tests ThingsBoard servers with high volumes of concurrent MQTT/HTTP/LWM2M messages from simulated devices. The tool can simulate thousands of IoT devices publishing telemetry data simultaneously.

**Version:** 4.0.1
**Java Version:** 17
**Build Tool:** Maven
**Main Class:** `org.thingsboard.tools.PerformanceTestApplication`

## Common Build and Test Commands

### Build the project (without Docker)
```bash
mvn clean install
```

### Build the project with Docker image
```bash
mvn clean install -Ddockerfile.skip=false
# Or use the convenience script:
./build.sh
```

### Run tests locally
```bash
# Using Maven directly
mvn spring-boot:run

# Using the convenience script (pre-configured with defaults)
./start.sh

# Run with custom environment variables
export REST_URL=http://127.0.0.1:8080
export MQTT_HOST=127.0.0.1
export DEVICE_END_IDX=1000
export MESSAGES_PER_SECOND=50
mvn spring-boot:run
```

### Run tests via Docker
```bash
# Using environment file
docker run -it --env-file .env --name tb-perf-test thingsboard/tb-ce-performance-test:latest

# Quick local test (network host mode)
docker run -it --rm --network host --pull always --log-driver none --name tb-perf-test thingsboard/tb-ce-performance-test:latest

# With inline environment variables
docker run -it --rm --network host --name tb-perf-test \
  --env REST_URL=http://127.0.0.1:8080 \
  --env MQTT_HOST=127.0.0.1 \
  --env DEVICE_END_IDX=1000 \
  --env MESSAGES_PER_SECOND=50 \
  thingsboard/tb-ce-performance-test:latest
```

### License management
```bash
# Format license headers
mvn license:format
```

### Build multi-architecture Docker images (AMD64 + ARM64)
```bash
mvn clean install -P push-docker-amd-arm-images
```

## Architecture Overview

### Test Execution Flow

1. **PerformanceTestApplication** - Spring Boot entry point
2. **PerformanceTestRunner** - ApplicationRunner that orchestrates test execution via TestExecutor
3. **TestExecutor** implementations:
   - **DeviceBaseTestExecutor** - Tests direct device-to-platform communication
   - **GatewayBaseTestExecutor** - Tests gateway API (single gateway managing multiple devices)
   - **LwM2MClientBaseTestExecutor** - Tests LWM2M protocol

### Key Component Layers

#### Service Layer (`org.thingsboard.tools.service`)
- **shared/** - Base classes and common test infrastructure
  - `BaseTestExecutor` - Abstract test executor with lifecycle management (init, warmup, test, cleanup)
  - `AbstractAPITest` - Common test logic
  - `RestClientService` - ThingsBoard REST API client wrapper

- **device/** - Device API test implementations
  - `MqttDeviceAPITest` - MQTT device protocol testing
  - `HttpDeviceAPITest` - HTTP device protocol testing
  - `Lwm2mDeviceAPITest` - LWM2M device protocol testing
  - `DeviceProfileManager` - Manages device profiles (SMART_TRACKER, SMART_METER, INDUSTRIAL_PLC)

- **gateway/** - Gateway API test implementations
  - `MqttGatewayAPITest` - Tests MQTT Gateway API

- **msg/** - Message generation
  - Payload type generators: smartTracker/, smartMeter/, industrialPLC/, random/
  - Each has separate telemetry and attributes generators

- **mqtt/** - MQTT client implementation
  - `DeviceClient` - Handles MQTT connections and message publishing

- **lwm2m/** - LWM2M protocol support
  - client/ - LWM2M client implementation
  - secure/ - Security configurations (PSK, RPK, X509)

#### Configuration (`src/main/resources`)
- **tb-ce-performance-tests.yml** - Main configuration file with all test parameters
- **device/profile/** - Device profile JSONs (smart_tracker.json, smart_meter.json, industrial_plc.json)
- **root_rule_chain_*.json** - ThingsBoard rule chain configurations for testing
- **credentials/** - LWM2M device credentials configurations

### Test Lifecycle

1. **Initialization** - Connect to ThingsBoard REST API, authenticate
2. **Device Profile Creation** - Create device profiles based on payload type
3. **Entity Creation** (optional) - Create customers, dashboards, devices, gateways
4. **Rule Chain Update** (optional) - Replace root rule chain with test-specific chain
5. **Warmup** (optional) - Send initial batch of messages to warm up connections
6. **Test Execution** - Publish messages at configured rate for specified duration
7. **Cleanup** - Revert rule chains, delete created entities (if configured)
8. **Shutdown** - Close connections and exit

### Payload Types

- **DEFAULT** - Basic telemetry
- **SMART_TRACKER** - GPS tracker: `{"latitude": 42.222222, "longitude": 73.333333, "speed": 55.5, "fuel": 92, "batteryLevel": 81}`
- **SMART_METER** - Utility meter: `{"pulseCounter": 1234567, "leakage": false, "batteryLevel": 81}`
- **INDUSTRIAL_PLC** - Industrial sensors: `{"line001": 1.0023, "line002": 95.440321, ...}` (configurable datapoints, default 60)
- **RANDOM** - Random telemetry values

## Key Configuration Parameters

All configuration is via environment variables or `tb-ce-performance-tests.yml`:

**Connection:**
- `REST_URL` - ThingsBoard REST API URL (default: http://localhost:8080)
- `REST_USERNAME` / `REST_PASSWORD` - Login credentials
- `MQTT_HOST` / `MQTT_PORT` - MQTT broker connection
- `MQTT_SSL_ENABLED` / `MQTT_SSL_KEY_STORE` - MQTT TLS configuration

**Test Parameters:**
- `DEVICE_API` - Protocol: MQTT, HTTP, or LWM2M
- `TEST_API` - Test mode: device (direct) or gateway
- `TEST_PAYLOAD_TYPE` - Payload type (see above)
- `DEVICE_START_IDX` / `DEVICE_END_IDX` - Device ID range
- `MESSAGES_PER_SECOND` - Message publishing rate
- `DURATION_IN_SECONDS` - Test duration
- `ALARMS_PER_SECOND` - Alarm generation rate

**Lifecycle Control:**
- `DEVICE_CREATE_ON_START` - Create devices before test
- `DEVICE_DELETE_ON_COMPLETE` - Delete devices after test
- `WARMUP_ENABLED` - Enable warmup phase
- `UPDATE_ROOT_RULE_CHAIN` - Replace root rule chain with test chain
- `REVERT_ROOT_RULE_CHAIN` - Restore original rule chain after test

## Development Notes

### Test Customization

To add a new payload type:
1. Create new package under `service/msg/yourtype/`
2. Implement `YourTypeTelemetryGenerator` extending `BaseMessageGenerator`
3. Implement `YourTypeAttributesGenerator` (optional)
4. Update `TEST_PAYLOAD_TYPE` enum handling
5. Add device profile JSON in `resources/device/profile/`

### Device Management

Devices are identified by index and use tokens like `device_token_0`, `device_token_1`, etc. The REST API creates devices, then test clients connect using these tokens.

### Protocol Support

- **MQTT**: Full support via Netty-based MQTT client
- **HTTP**: REST API for telemetry/attributes
- **LWM2M**: CoAP-based protocol with security modes (NoSec, PSK, RPK, X509)

### Dependencies

Main dependencies:
- Spring Boot 3.2.12 (Web, Security, Actuator)
- ThingsBoard 4.0.1 (REST client, MQTT client, data models)
- Netty 4.1.121 (MQTT transport)
- Eclipse Leshan 2.0.0-M4 (LWM2M)
- Lombok 1.18.38 (code generation)

## Project Structure

```
src/main/java/org/thingsboard/tools/
├── PerformanceTestApplication.java    # Spring Boot main
├── PerformanceTestRunner.java         # Test orchestrator
└── service/
    ├── shared/                        # Base test infrastructure
    ├── device/                        # Device API tests
    ├── gateway/                       # Gateway API tests
    ├── mqtt/                          # MQTT client
    ├── msg/                           # Message generators
    ├── lwm2m/                         # LWM2M implementation
    ├── customer/                      # Customer management
    ├── dashboard/                     # Dashboard management
    └── rule/                          # Rule chain management

src/main/resources/
├── tb-ce-performance-tests.yml        # Main config
├── device/profile/                    # Device profiles
├── credentials/                       # LWM2M credentials
└── *.json                             # Dashboards, rule chains
```

## Docker Build

The project uses multi-stage Maven build + Debian package (`.deb`) deployment in Docker. The Dockerfile installs the `.deb` package generated by Maven/Gradle.

Base image: `thingsboard/openjdk17:bookworm-slim`

## Testing Strategy

This tool measures:
- **Throughput**: Messages/second successfully published
- **Connection stability**: Number of devices that can connect simultaneously
- **System load**: How ThingsBoard handles high message rates
- **Alarm generation**: Performance under alarm storm conditions

Results help determine ThingsBoard server capacity and scaling requirements.

## Code Generation
Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.
