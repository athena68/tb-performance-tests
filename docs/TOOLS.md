# Development Tools & Utilities

## Overview

This document describes the development tools, utilities, and scripts available in the ThingsBoard Performance Tests project.

## Python Scripts

### Provisioning Scripts

#### provision-scenario.py

**Purpose**: Main provisioning script for creating ThingsBoard entities from JSON scenarios.

**Usage**:
```bash
python3 test-scenarios/provision-scenario.py \
  <scenario-file> \
  --credentials test-scenarios/credentials.json \
  [--no-config-attrs] \
  [--env-file .env] \
  [--no-env-file]
```

**Features**:
- Creates sites, buildings, floors, rooms, gateways, and devices
- Sets device credentials automatically
- Generates .env file for Java app
- Configurable attributes from YAML templates
- Idempotent (safe to run multiple times)

**Options**:
- `--credentials <file>`: Credentials JSON file path
- `--url <url>`: ThingsBoard URL (alternative to credentials file)
- `--username <user>`: ThingsBoard username
- `--password <pass>`: ThingsBoard password
- `--no-config-attrs`: Disable configurable attributes, use fallback values
- `--env-file <name>`: .env output filename (default: `.env`)
- `--no-env-file`: Skip .env file generation

**Example**:
```bash
python3 test-scenarios/provision-scenario.py \
  test-scenarios/scenario-hanoi-cleanroom.json \
  --credentials test-scenarios/credentials.json
```

#### cleanup-scenario.py

**Purpose**: Clean up ThingsBoard entities created by provisioning scripts.

**Usage**:
```bash
python3 test-scenarios/cleanup-scenario.py \
  --credentials test-scenarios/credentials.json \
  [--assets] \
  [--devices] \
  [--confirm]
```

**Features**:
- Delete all customer assets
- Delete all customer devices (including gateways)
- Requires explicit `--confirm` flag for safety
- Shows entity counts before deletion

**Options**:
- `--credentials <file>`: Credentials JSON file path
- `--assets`: Delete all assets
- `--devices`: Delete all devices
- `--confirm`: Confirm deletion (required)

**Example**:
```bash
# Delete both assets and devices
python3 test-scenarios/cleanup-scenario.py \
  --credentials test-scenarios/credentials.json \
  --assets --devices --confirm

# Delete devices only
python3 test-scenarios/cleanup-scenario.py \
  --credentials test-scenarios/credentials.json \
  --devices --confirm
```

## Shell Scripts

### Test Runners

#### start-ebmpapst-gateway.sh

**Location**: `scripts/test-runners/`

**Purpose**: Run gateway performance test with ebmpapst FFU payload.

**Usage**:
```bash
./scripts/test-runners/start-ebmpapst-gateway.sh
```

**Features**:
- Sources .env file for configuration
- Validates required environment variables
- Runs Maven Spring Boot application
- Logs output to file

### Utility Scripts

#### check-local-server.sh

**Purpose**: Verify local ThingsBoard server is accessible.

**Usage**:
```bash
./check-local-server.sh
```

**Checks**:
- HTTP API accessibility
- Authentication endpoint
- Device count
- Gateway count

#### check-server-stability.sh

**Purpose**: Monitor ThingsBoard server stability over time.

**Usage**:
```bash
./check-server-stability.sh
```

**Features**:
- Periodic health checks
- Connection monitoring
- Log aggregation
- Alert on failures

#### test-provision.sh

**Purpose**: Test provisioning script with common scenarios.

**Usage**:
```bash
./test-provision.sh
```

**Features**:
- Runs provision script with test scenarios
- Verifies entity creation
- Checks .env generation
- Reports results

## Configuration Files

### Scenario Files

**Location**: `test-scenarios/scenario-*.json`

**Format**:
```json
{
  "scenarioName": "Test Scenario",
  "description": "Description of test scenario",
  "testConfig": {
    "messagesPerSecond": 60,
    "durationInSeconds": 86400,
    "payloadType": "EBMPAPST_FFU"
  },
  "site": {
    "name": "Site Name",
    "type": "Site",
    "latitude": 21.0285,
    "longitude": 105.8542
  },
  "buildings": [
    {
      "name": "Building Name",
      "floors": [
        {
          "name": "Floor Name",
          "rooms": [
            {
              "name": "Room Name",
              "gateways": [
                {
                  "name": "GW00000000",
                  "devices": {
                    "prefix": "DW",
                    "start": 0,
                    "end": 29,
                    "count": 30
                  }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Credentials File

**Location**: `test-scenarios/credentials.json`

**Format**:
```json
{
  "thingsboard": {
    "url": "http://localhost:8080",
    "username": "tenant@thingsboard.org",
    "password": "tenant",
    "mqtt_host": "localhost",
    "mqtt_port": 1883
  }
}
```

**Security**: This file is gitignored. Use `credentials.json.example` as template.

### Attribute Templates

**Location**: `config/attributes/*.yml`

**Purpose**: Define configurable attributes for entities.

**Example** (`config/attributes/ebmpapstffu.yml`):
```yaml
attributes:
  - name: fan_model
    type: string
    values:
      - "EC-K 500"
      - "EC-K 630"
      - "EC-K 800"

  - name: nominal_power
    type: number
    min: 500
    max: 2000
    unit: "W"

  - name: max_airflow
    type: number
    min: 1000
    max: 5000
    unit: "m³/h"
```

## Build Tools

### Maven

**Build Project**:
```bash
mvn clean install
```

**Run Tests**:
```bash
mvn test
```

**Run Application**:
```bash
mvn spring-boot:run
```

**Package JAR**:
```bash
mvn clean package -DskipTests
```

**Build Docker Image**:
```bash
mvn clean install -Ddockerfile.skip=false
```

### Docker

**Build Image**:
```bash
docker build -t tb-perf-test .
```

**Run Container**:
```bash
docker run -it --rm --network host \
  --env-file .env \
  --name tb-perf-test \
  tb-perf-test
```

**Multi-Architecture Build**:
```bash
mvn clean install -P push-docker-amd-arm-images
```

## Development Environment

### Required Tools

- **Java 17**: JDK for building and running Java application
- **Maven 3.6+**: Build tool and dependency management
- **Python 3.8+**: For provisioning scripts
- **Docker** (optional): For containerized deployment

### Python Dependencies

Install via pip:
```bash
pip3 install requests pyyaml
```

### IDE Setup

#### IntelliJ IDEA

1. Import as Maven project
2. Set SDK to Java 17
3. Enable Lombok plugin
4. Configure code style (see `.editorconfig`)

#### VS Code

1. Install extensions:
   - Extension Pack for Java
   - Spring Boot Extension Pack
   - Python
2. Open folder in VS Code
3. Configure Python interpreter

## Testing Utilities

### Manual Device Connection Test

```bash
# Test MQTT connection
mosquitto_pub -h localhost -p 1883 \
  -u "GW00000000" \
  -t "v1/gateway/telemetry" \
  -m '{"temperature": 25}'

# Test HTTP connection
curl -X POST http://localhost:8080/api/v1/GW00000000/telemetry \
  -H "Content-Type: application/json" \
  -d '{"temperature": 25}'
```

### Query ThingsBoard API

```bash
# Get auth token
TOKEN=$(curl -s -X POST "http://localhost:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"tenant@thingsboard.org","password":"tenant"}' \
  | jq -r '.token')

# List devices
curl -s -X GET "http://localhost:8080/api/tenant/devices?pageSize=100&page=0" \
  -H "X-Authorization: Bearer $TOKEN" \
  | jq '.data[] | {name: .name, type: .type}'

# Get device credentials
DEVICE_ID="<device-id>"
curl -s -X GET "http://localhost:8080/api/device/$DEVICE_ID/credentials" \
  -H "X-Authorization: Bearer $TOKEN" \
  | jq '{credentialsType, credentialsId}'
```

## AI Development Tools

### Claude Code

This project includes a `CLAUDE.md` file with instructions for Claude Code (claude.ai/code) to assist with development.

**Features**:
- Context-aware code suggestions
- Automated refactoring assistance
- Documentation generation
- Test scenario creation

**Usage**: Claude Code automatically reads `CLAUDE.md` when working in this repository.

### Code Generation with Context7

The project is configured to use Context7 MCP for library documentation and code generation.

**Available Libraries**:
- ThingsBoard REST API
- Spring Boot
- MQTT/Netty
- Eclipse Leshan (LWM2M)

**Example Usage**:
```
Ask Claude: "Generate a new payload type for industrial sensors using Context7"
Claude will:
1. Lookup ThingsBoard documentation via Context7
2. Generate appropriate Java classes
3. Update configuration files
4. Provide usage examples
```

## Performance Profiling

### JVM Profiling

```bash
# Enable JMX monitoring
export MAVEN_OPTS="-Dcom.sun.management.jmxremote \
  -Dcom.sun.management.jmxremote.port=9010 \
  -Dcom.sun.management.jmxremote.authenticate=false \
  -Dcom.sun.management.jmxremote.ssl=false"

mvn spring-boot:run

# Connect with JConsole
jconsole localhost:9010
```

### Memory Analysis

```bash
# Generate heap dump
jmap -dump:live,format=b,file=heap.bin <pid>

# Analyze with Eclipse MAT or VisualVM
```

## Logging Configuration

### Log Levels

Edit `src/main/resources/logback.xml`:

```xml
<!-- Set to DEBUG for detailed logs -->
<logger name="org.thingsboard.tools" level="INFO"/>

<!-- MQTT client logs -->
<logger name="io.netty.handler.logging" level="DEBUG"/>

<!-- ThingsBoard REST client -->
<logger name="org.thingsboard.server.common.data.rest" level="DEBUG"/>
```

### Log Output

```bash
# Console output (default)
mvn spring-boot:run

# File output
mvn spring-boot:run > performance-test.log 2>&1

# Follow logs in real-time
tail -f performance-test.log
```

## CI/CD Integration

### GitHub Actions (Example)

```yaml
name: Performance Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up JDK 17
      uses: actions/setup-java@v2
      with:
        java-version: '17'
        distribution: 'adopt'

    - name: Build with Maven
      run: mvn clean install -DskipTests

    - name: Run unit tests
      run: mvn test
```

## Useful Commands Cheat Sheet

```bash
# Quick provision and test
python3 test-scenarios/provision-scenario.py \
  test-scenarios/scenario-hanoi-cleanroom.json \
  --credentials test-scenarios/credentials.json && \
source .env && mvn spring-boot:run

# Full cleanup and restart
python3 test-scenarios/cleanup-scenario.py \
  --credentials test-scenarios/credentials.json \
  --assets --devices --confirm && \
mvn clean && \
rm -f .env

# Check current setup
ls -1 *.sh
ls -1 test-scenarios/*.json
git status --short

# Build and run Docker
mvn clean install -Ddockerfile.skip=false && \
docker run -it --rm --network host --env-file .env tb-perf-test

# Health check
./check-local-server.sh && \
./check-server-stability.sh
```
